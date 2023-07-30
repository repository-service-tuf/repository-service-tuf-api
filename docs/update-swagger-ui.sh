#!/bin/sh
#
# Script to update docs/dist to the latest Swagger UI.
# Based on https://github.com/peter-evans/swagger-github-pages/blob/master/.github/workflows/update-swagger.yml.
# $1 argument: Optionally pass "check". When passing "check" we see if there's an update and if yes, it will exit
# with a fail code.


# Exit when any command fails
set -e

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPT_PATH=$(dirname "$SCRIPT")

# Get Latest Swagger UI Release
# https://github.com/swagger-api/swagger-ui/releases/latest redirects to a URL format of https://github.com/swagger-api/swagger-ui/git-lfs/releases/tag/vx.y.z
RELEASE_TAG=$(curl -Ls -o /dev/null -w %{url_effective} https://github.com/swagger-api/swagger-ui/releases/latest | awk -F/ '{print $NF}')
echo "Swagger UI release_tag=$RELEASE_TAG"

CURRENT_TAG=$(cat $SCRIPT_PATH/swagger-ui.version)
echo "Swagger UI current_tag=$CURRENT_TAG"

UPDATE="false"
if [ $CURRENT_TAG != $RELEASE_TAG ]; then
  UPDATE="true"
fi

# Update Swagger UI
if [ $UPDATE = "true" ]; then

  # If there's a possible update and we are specifically checking for it
  if [ -n "$1" ] && [ $1 = "check" ]; then
    echo "CHECK FAILED: An update is required to Swagger UI (docs/dist/)."
    exit 1

  else
    SWAGGER_JSON="swagger.json"
    # Delete the dist directory and index.html
    rm -fr $SCRIPT_PATH/dist $SCRIPT_PATH/index.html

    # Download the release
    curl -sL -o $SCRIPT_PATH/$RELEASE_TAG https://api.github.com/repos/swagger-api/swagger-ui/tarball/$RELEASE_TAG

    # Extract the dist directory from the tar file
    mkdir $SCRIPT_PATH/dist
    dir_to_extract="$(tar -tzf $SCRIPT_PATH/$RELEASE_TAG | head -1 | cut -f1 -d"/")/dist"
    tar -xzf $SCRIPT_PATH/$RELEASE_TAG -C $SCRIPT_PATH --strip-components=1 $dir_to_extract
    rm $SCRIPT_PATH/$RELEASE_TAG

    # Move index.html to the root
    mv $SCRIPT_PATH/dist/index.html $SCRIPT_PATH

    # Fix references in dist/swagger-initializer and index.html
    sed -i "s|https://petstore.swagger.io/v2/swagger.json|$SWAGGER_JSON|g" $SCRIPT_PATH/dist/swagger-initializer.js
    sed -i "s|href=\"./|href=\"dist/|g" $SCRIPT_PATH/index.html
    sed -i "s|src=\"./|src=\"dist/|g" $SCRIPT_PATH/index.html
    sed -i "s|href=\"index|href=\"dist/index|g" $SCRIPT_PATH/index.html

    # Update current release
    echo $RELEASE_TAG > $SCRIPT_PATH/swagger-ui.version

    echo "Swagger UI is updated!"

  fi

else
  echo "No update required to Swagger UI (docs/dist/)."

fi
