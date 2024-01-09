#!/usr/bin/env python3

import argparse
import asyncio
import re
import semver
import subprocess
import tempfile
import yaml

from aiohttp import ClientSession
from pathlib import Path

CONAN_NEMTECH_REMOTE = 'https://conan.symbol.dev/artifactory/api/conan/catapult'
RECIPES_REPOSITORIES = {
	'benchmark': 'google',
	'mongo-c-driver': 'mongodb',
	'mongo-cxx-driver': 'mongodb',
	'libzmq': 'zeromq',
	'cppzmq': 'zeromq',
	'rocksdb': 'facebook'
}
RECIPES = RECIPES_REPOSITORIES.keys()
DEPENDENCY_MAP = {'mongo-cxx-driver': 'mongo-c-driver', 'cppzmq': 'zeromq'}
REPO_RECIPE_MAP = {'libzmq': 'zeromq'}


def dispatch_subprocess(command_line, cwd=None, handle_error=True):
	print(' '.join(command_line))
	result = subprocess.run(command_line, check=False, cwd=cwd, capture_output=True)
	if handle_error and 0 != result.returncode:
		raise subprocess.SubprocessError(f'command failed with exit code {result.returncode}\n{result}')

	output = result.stdout if 0 == result.returncode else result.stderr
	decode_output = output.decode('utf-8')
	if decode_output:
		print(decode_output)

	return decode_output, result.returncode


def update_recipe_version(current_version, new_version, filepath):
	dispatch_subprocess(
		['sed', '-i', f's/{current_version}/{new_version}/g', str(filepath)],
		handle_error=True
	)


def initialize_conan():
	dispatch_subprocess(['conan', 'config', 'init'])
	dispatch_subprocess(['conan', 'config', 'set', 'general.revisions_enabled=1'])
	dispatch_subprocess(['conan', 'profile', 'update', 'settings.compiler.libcxx=libstdc++11', 'default'])
	dispatch_subprocess(['conan', 'remote', 'add', '--force', 'nemtech', CONAN_NEMTECH_REMOTE])


class RecipeHelper:
	def __init__(self, dependency_map, repo_recipe_map):
		self.dependency_map = dependency_map
		self.repo_recipe_map = repo_recipe_map

	def update_recipe_dependent_version(self, recipes_versions, recipe_path):
		for recipe, recipe_dependent in self.dependency_map.items():
			versions = recipes_versions.get(recipe_dependent)
			print(f'checking dependent version {recipe}, {recipe_dependent} {versions}')
			if versions:
				current_version, new_version = versions
				update_recipe_version(current_version, new_version, recipe_path / f'{recipe}/all/conanfile.py')

	def get_recipe_name(self, repo_name):
		return self.repo_recipe_map.get(repo_name, repo_name)


class CatapultRecipesUpdater:
	def __init__(self, source_path, recipe_helper):
		self.source_path = Path(source_path).absolute()
		self.recipe_helper = recipe_helper

	@staticmethod
	async def _get_recipe_latest_version(owner, repo):
		url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
		async with ClientSession(raise_for_status=True) as session:
			async with session.get(url) as response:
				response_json = await response.json()
				if 200 != response.status:
					raise Exception(f'failed to get latest release for {owner}/{repo} {response_json}')
				return re.sub(r'[^\d\.]', '', response_json['tag_name'])

	@staticmethod
	async def _read_yaml_file(filepath):
		with open(filepath, 'rt') as file:
			return yaml.safe_load(file)

	async def _get_current_version(self, name):
		recipe_config_filepath = self.source_path / f'{name}/config.yml'
		config = await self._read_yaml_file(recipe_config_filepath)
		return next(iter(config['versions'].keys()))

	async def _get_update_if_available(self, recipe_repo):
		owner = RECIPES_REPOSITORIES[recipe_repo]
		latest_version = await self._get_recipe_latest_version(owner, recipe_repo)
		recipe = self.recipe_helper.get_recipe_name(recipe_repo)
		current_version = await self._get_current_version(recipe)
		print(f'checking recipe {recipe} {current_version} -> {latest_version}')
		if semver.compare(latest_version, current_version) > 0:
			print(f'{recipe} has new version: {latest_version}')
			return recipe, current_version, latest_version

		return None

	async def get_available_updates(self, recipes):
		results = await asyncio.gather(*[self._get_update_if_available(recipe) for recipe in recipes])
		return {result[0]: (result[1], result[2]) for result in results if result}

	async def _update_conandata_sha(self, recipe, filepath, version):
		config = await self._read_yaml_file(filepath)
		url = config['sources'][version]['url']
		with tempfile.TemporaryDirectory() as tmpdir:
			tmp_source_filepath = f'{tmpdir}/{recipe}.{version}.tar.gz'
			dispatch_subprocess(['curl', '-LJ', url, '--output', f'{tmp_source_filepath}'])
			output, _ = dispatch_subprocess(['sha256sum', f'{tmp_source_filepath}'], handle_error=True)
			config['sources'][version]['sha256'] = output.split(' ')[0]
			with open(filepath, 'w') as output_file:
				yaml.dump(config, output_file, sort_keys=False)

	async def _update_recipe_files(self, recipe, versions, recipes_versions):
		update_recipe_files_descriptor = [
			r'{recipe}/config.yml',
			r'{recipe}/all/conandata.yml',
			r'{recipe}/all/test_package/CMakeLists.txt',
		]

		print(f'updating recipe {recipe} {versions}')
		for recipe_file_descriptor in update_recipe_files_descriptor:
			recipe_file = recipe_file_descriptor.format(recipe=recipe)
			recipe_filepath = self.source_path / recipe_file
			if recipe_filepath.exists():
				current_version, new_version = versions
				update_recipe_version(current_version, new_version, recipe_filepath)
				if 'conandata.yml' == recipe_filepath.name:
					await self._update_conandata_sha(recipe, recipe_filepath, new_version)

	async def update_recipes_version(self, recipes_versions):
		print(f'updating recipes {recipes_versions}')
		await asyncio.gather(*[
			self._update_recipe_files(recipe, versions, recipes_versions) for recipe, versions in recipes_versions.items()
		])

		self.recipe_helper.update_recipe_dependent_version(recipes_versions, self.source_path)

	async def _execute_conan_package_command(self, recipes_versions, get_command):
		for recipe, versions in recipes_versions.items():
			_, new_version = versions
			recipe_path = self.source_path / f'{recipe}/all'
			dispatch_subprocess(
				get_command(new_version, recipe),
				cwd=recipe_path,
				handle_error=True
			)

	async def build_conan_package(self, recipes_versions):
		await self._execute_conan_package_command(
			recipes_versions,
			lambda version, recipe_name: ['conan', 'create', '.', f'{version}@nemtech/stable', '--build=missing', '--remote=nemtech']
		)

	async def upload_conan_package(self, recipes_versions):
		await self._execute_conan_package_command(
			recipes_versions,
			lambda version, recipe_name: ['conan', 'upload', f'{recipe_name}/{version}@nemtech/stable', '--remote=nemtech']
		)


async def main():
	parser = argparse.ArgumentParser(description='Recipes updater for catapult')
	parser.add_argument('--commit-title', help='commit title')
	parser.add_argument('--recipes', choices=RECIPES, help='recipes to update', default=RECIPES)
	parser.add_argument('--recipes-path', help='path to the recipes', required=True)
	parser.add_argument('--upload', help='upload recipes to conan', action='store_true')
	args = parser.parse_args()

	recipe_helper = RecipeHelper(DEPENDENCY_MAP, REPO_RECIPE_MAP)
	recipes_updater = CatapultRecipesUpdater(args.recipes_path, recipe_helper)
	recipes_to_update = await recipes_updater.get_available_updates(args.recipes)
	if not recipes_to_update:
		print('no recipe to update')
		return

	print(f'recipes to update - {recipes_to_update}')
	await recipes_updater.update_recipes_version(recipes_to_update)
	initialize_conan()
	await recipes_updater.build_conan_package(recipes_to_update)

	if args.upload:
		await recipes_updater.upload_conan_package(recipes_to_update)

	update_message = '\n'.join([f'{recipe} {versions[0]} -> {versions[1]}' for recipe, versions in recipes_to_update.items()])
	print(f'updated recipe:\n{update_message}')
	if args.commit_title:
		dispatch_subprocess(['git', 'add', '.'])
		dispatch_subprocess(['git', 'commit', '-m', f'{args.commit_title}\n\n{update_message}'])


if '__main__' == __name__:
	asyncio.run(main())
