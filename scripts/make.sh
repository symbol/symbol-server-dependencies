#!/bin/bash

prog=$0
recipes="openssl mongo-c-driver mongo-cxx-driver benchmark zeromq cppzmq milagro rocksdb"

function help {
cat << EOF
$prog <recipe|all>
	Builds the conan packages specified by recipe name (all versions in config.yml file).
	If binaries are already available in ~/.conan/data it exits immediately with success.

	Available recipes:
	$recipes
EOF
}

function recipe {
	name=$1
	echo "recipe $name"
	dir=recipes/$name
	pushd ${dir} > /dev/null
		for v in `cat config.yml | grep -v "version" | grep -v "folder" | grep ".*:$" | sed "s/\"//g" | sed "s/://g" | sed "s/ //g"`; do
			dir=`cat config.yml | grep "$v" -A1 | tail -n1 | sed "s/ *folder: *\(.*\)/\1/" | sed "s/\"//g"`
			echo "conan info $name/$v@nemtech/stable dir $dir"
			conan info $name/$v@nemtech/stable | grep "Binary: Cache"
			if [ $? -eq 0 ]; then
				echo "$name/$v@nemtech/stable already built."
				continue
			fi
			pushd $dir > /dev/null
				echo "conan create . $v@nemtech/stable"
				conan create . $v@nemtech/stable
			popd > /dev/null
		done
	popd > /dev/null
	echo "end recipe"
}

rcp=$1
shift

if [ "_$rcp" == "_all" ]; then
	for r in $recipes; do
		recipe $r
	done
	exit 0
else
	if [ -f recipes/$rcp/config.yml ]; then
		recipe $rcp
		exit 0
	fi
fi
echo "Error: Invalid recipe $rcp"
echo "help:"
#error flow
help
exit 1
