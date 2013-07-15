#!/bin/bash
#
# Ask the necessary questions to the user and publish a new version
# of the package in pypi
#
which vim > /dev/null
if [ $? -ne 0 ];then
  echo 'Missing vim. Seriously?'
  exit 1
fi

which ruby > /dev/null
if [ $? -ne 0 ];then
  echo 'Missing ruby.'
  exit 1
fi

ONE=`cat setup.py | grep "version" | ruby -ne 'puts $_.match(/([\d\.]+)\"/)[1]'`
TWO=`cat librato/__init__.py | grep "^__version__" | ruby -ne 'puts $_.match(/([\d\.]+)\"/)[1]'`
THREE=`cat CHANGELOG.md  | grep Version | head -1 | awk '{print $3}'`

echo "Current version detected (setup|init|changelog): $ONE $TWO $THREE"
echo -ne "Introduce new version: "
read NEW
export _NEW=$NEW

echo "* Introduce your message here." > _tmp
vim _tmp
MSG=`cat _tmp`
rm _tmp

CHL_MSG=<<EOF
### Version $NEW
* $MSG
EOF

cat setup.py            | ruby -ne 'puts $_.gsub(/version = \"[\d\.]+\"/, "version = \"" + ENV["_NEW"] + "\"" )'	> _tmp
mv _tmp setup.py
cat librato/__init__.py | ruby -ne 'puts $_.gsub(/__version__ = \"[\d\.]+\"/,  "__version__ = \"" + ENV["_NEW"] + "\"")'  > _tmp
mv _tmp librato/__init__.py
( echo -e "## Changelog\n" ; echo "### Version $NEW"; echo "$MSG"; cat CHANGELOG.md | grep -v Change)  > _tmp
mv _tmp CHANGELOG.md
rm -f _tmp

echo ""
git diff
echo ""
echo -ne "Hit <enter> to send new package to pypi; <ctrl+c> to cancel..."
read

python setup.py sdist upload
