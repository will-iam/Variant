#!/bin/bash
param=%1%2%3%4

#LAST_TAG = env.Command([], LAST_TAG_COMMIT,'git describe --tags $SOURCE')
#	DEFINES += VERSIONTAG=\"$${LAST_TAG}\"
#	message(Last Git Tag = $$LAST_TAG)

# total number of commits
#	BUILD      = $$system(git log --oneline | wc -l | sed -e "s/[\t]*//g")
#	DEFINES += BUILDNUMBER=\"$${BUILD}\"

LAST_TAG_COMMIT=$(git rev-list master --tags --max-count=1);
LAST_TAG=$(git describe --tags $LAST_TAG_COMMIT);
BUILD=$(git log --oneline | wc -l | sed -e "s/[\t]*//g");
#echo "$LAST_TAG_COMMIT, $LAST_TAG, $BUILD";

currentSystem=$(uname -s)
currentMachine=$(uname -n)
currentUser=$(id -u -n)
workspace="/home/$currentUser/workspace/"

if test $currentSystem = "Darwin"
	then
	workspace="/Users/$currentUser/workspace/"
fi

echo "Current Machine Name: $currentMachine, logged as $currentUser";

if test $# -lt 1
then
	echo "Zero argument, exit.";
	exit 1;
fi

if test $# -lt 2
then
	echo "Only 1 argument, exit.";
	exit 1;
fi

buildv=$(echo $BUILD | bc);

# Define the default library folder.
lib="linux";

if test $# -gt 2
    then
    if test $3 = "clean"
		then
		echo "Clean the build";
		scons -c workspace=$workspace project=$1 mode=$2 tag=$LAST_TAG buildv=$buildv compiler=gnu lib=$lib
		scons -c workspace=$workspace project=$1 mode=$2 tag=$LAST_TAG buildv=$buildv compiler=clang lib=$lib
		exit 0;
    fi
    lib=$3;
fi

tool="scons";
compilerArray=( "gnu" "clang" )
for compiler in "${compilerArray[@]}"
	do
		echo "$tool workspace=$workspace project=$1 mode=$2 tag=$LAST_TAG buildv=$buildv compiler=$compiler lib=$lib";
		$tool workspace=$workspace project=$1 mode=$2 tag=$LAST_TAG buildv=$buildv compiler=$compiler lib=$lib
		prog="$1-$2-$compiler";
		if [ -f $prog ]
			then
				rm $prog;
				if [ -f ../script/start-$1.sh ]
    				then
					cp ../script/start-$1.sh ${workspace}${prog}/
				fi
			else
				echo "$prog does not exits, build failed";
    			exit 1;
		fi
done

# Return if it is a single compilation.
if test $# -gt 3 && test $4 = "single"
	then
	exit 0;
fi

# build all in order to test regression in shared code: maxidebug, debug, profile, release on gnu, clang, intel.
projectArray=( "optionprice" "optionchain" "scanner" "closer" "publisher" "uatp" "accountmanager")
modeArray=( "maxidebug" "debug" "profile" "release")

for project in "${projectArray[@]}"
	do
	for mode in "${modeArray[@]}"
	do
		if [ "$project" = "$1" ] && [ "$mode" = "$2" ]
			then
			continue;
		fi
		./build.sh $project $mode clean
		./build.sh $project $mode $lib single
		if [ $? != 0 ]
			then
			echo "Could not compile everything."
			exit 1;
		fi
	done
done


# build unit tests
./build.sh common/rabbitmq/unittest $mode clean
./build.sh common/rabbitmq/unittest $mode $lib single
if [ $? != 0 ]
	then
	echo "Could not compile rabbitmq unit test."
	exit 1;
fi

# run unit tests
workspace/common/rabbitmq/unittest-$mode-gnu -s 127.0.0.1 -p 5672 -u guest -p guest
if [ $? != 0 ]
	then
	echo "Rabbitmq unit test failed."
	exit 1;
fi

exit 0;
