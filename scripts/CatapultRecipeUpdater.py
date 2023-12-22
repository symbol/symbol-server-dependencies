#!/usr/bin/env python3

import argparse
import asyncio
import re
import semver
import subprocess
import tempfile
import yaml
from collections import ChainMap

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


def dispatch_subprocess(command_line, cwd=None, handle_error=True):
	print(' '.join(command_line))
	result = subprocess.run(command_line, check=False, cwd=cwd, capture_output=True)
	if handle_error and 0 != result.returncode:
		raise subprocess.SubprocessError(f'command failed with exit code {result.returncode}\n{result}')

	output = result.stdout.decode('utf-8') if 0 == result.returncode else result.stderr.decode('utf-8')
	if output:
		print(output)

	return output, result.returncode


class CatapultRecipesUpdater:
	def __init__(self, source_path):
		self.source_path = Path(source_path).absolute()

	@staticmethod
	async def _initialize_conan():
		dispatch_subprocess(['conan', 'config', 'init'])
		dispatch_subprocess(['conan', 'config', 'set', 'general.revisions_enabled=1'])
		dispatch_subprocess(['conan', 'profile', 'update', 'settings.compiler.libcxx=libstdc++11', 'default'])
		dispatch_subprocess(['conan', 'remote', 'add', '--force', 'nemtech', CONAN_NEMTECH_REMOTE])

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
		with open(filepath, 'r') as file:
			return yaml.safe_load(file)

	async def _get_current_version(self, name):
		recipe_config_filepath = self.source_path / f'{name}/config.yml'
		config = await self._read_yaml_file(recipe_config_filepath)
		return next(iter(config['versions'].keys()))

	async def _get_update_if_available(self, recipe):
		owner = RECIPES_REPOSITORIES[recipe]
		recipe_update = {}
		latest_version = await self._get_recipe_latest_version(owner, recipe)
		recipe = 'zeromq' if 'libzmq' == recipe else recipe
		current_version = await self._get_current_version(recipe)
		print(f'checking recipe {recipe} {current_version} -> {latest_version}')
		if semver.compare(latest_version, current_version) > 0:
			print(f'{recipe} has new version: {latest_version}')
			recipe_update[recipe] = (current_version, latest_version)

		return recipe_update

	async def get_available_update(self, recipes):
		results = await asyncio.gather(*[self._get_update_if_available(recipe) for recipe in recipes])
		recipe_with_updates = dict(ChainMap(*results))
		return recipe_with_updates

	async def _update_conandata_sha(self, recipe, filepath, version):
		config = await self._read_yaml_file(filepath)
		url = config['sources'][version]['url']
		with tempfile.TemporaryDirectory() as tmpdir:
			download_file = f'{tmpdir}/{recipe}.{version}.tar.gz'
			dispatch_subprocess(['curl', '-LJ', url, '--output', f'{download_file}'])
			output, _ = dispatch_subprocess(['sha256sum', f'{download_file}'], handle_error=True)
			config['sources'][version]['sha256'] = output.split(' ')[0]
			with open(filepath, 'w') as output_file:
				yaml.dump(config, output_file, sort_keys=False)

	async def _update_recipe_files(self, recipe, versions, recipes_versions):
		update_recipe_files_descriptor = [
			r'{recipe}/config.yml',
			r'{recipe}/all/conandata.yml',
			r'{recipe}/all/test_package/CMakeLists.txt',
			r'{recipe}/all/conanfile.py',
		]
		dependency_map = {'mongo-cxx-driver': 'mongo-c-driver', 'cppzmq': 'zeromq'}

		print(f'updating recipe {recipe} {versions}')
		for recipe_file_descriptor in update_recipe_files_descriptor:
			recipe_file = recipe_file_descriptor.format(recipe=recipe)
			recipe_file_path = self.source_path / recipe_file
			if recipe_file_path.exists():
				if 'conanfile.py' == recipe_file_path.name:
					if recipe not in dependency_map.keys():
						continue

					dependency_recipe = dependency_map[recipe]
					if dependency_recipe not in recipes_versions.keys():
						continue

					current_version, new_version = recipes_versions[dependency_map[recipe]]
				else:
					current_version, new_version = versions

				dispatch_subprocess(
					['sed', '-i', f's/{current_version}/{new_version}/g', str(recipe_file_path)],
					handle_error=True
				)

				if 'conandata.yml' == recipe_file_path.name:
					await self._update_conandata_sha(recipe, recipe_file_path, new_version)

	async def update_recipe_version(self, recipes_versions):
		print(f'updating recipes {recipes_versions}')
		await asyncio.gather(*[
			self._update_recipe_files(recipe, versions, recipes_versions) for recipe, versions in recipes_versions.items()
		])

	async def build_conan_package(self, recipes_versions):
		await self._initialize_conan()
		for recipe, versions in recipes_versions.items():
			_, new_version = versions
			recipe_path = self.source_path / f'{recipe}/all'
			dispatch_subprocess(
				['conan', 'create', '.', f'{new_version}@nemtech/stable', '--remote=nemtech'],
				cwd=recipe_path,
				handle_error=True
			)

	async def upload_conan_package(self, recipes_versions):
		for recipe, versions in recipes_versions:
			_, new_version = versions
			recipe_path = self.source_path / f'{recipe}/all'
			dispatch_subprocess(
				['conan', 'upload', f'{recipe}/{new_version}@nemtech/stable', '--remote=nemtech'],
				cwd=recipe_path,
				handle_error=True
			)


async def main():
	parser = argparse.ArgumentParser(description='Recipes updater for catapult')
	parser.add_argument('--commit-title', help='commit title')
	parser.add_argument('--recipes', choices=RECIPES, help='recipes to update', default=RECIPES)
	parser.add_argument('--recipes-path', help='path to the recipes', required=True)
	parser.add_argument('--upload', help='upload recipes to conan', action='store_true')
	args = parser.parse_args()

	recipes_updater = CatapultRecipesUpdater(args.recipes_path)
	recipes_to_update = await recipes_updater.get_available_update(args.recipes)
	if not recipes_to_update:
		print('no recipe to update')
		return

	print(f'recipes to update - {recipes_to_update}')
	await recipes_updater.update_recipe_version(recipes_to_update)
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
