gitPullRequestPipeline {
	dockerImageName = 'symbolplatform/build-ci:cpp-ubuntu-lts'
	branchName = 'fix/update_catapult_recipe'
	scriptSetupCommand = 'python3 -m pip install -r scripts/requirements.txt'
	scriptCommand = 'python3 scripts/CatapultRecipeUpdater.py --recipes-path recipes --commit-title "[recipe] fix: update recipes"'
	reviewers = []
}
