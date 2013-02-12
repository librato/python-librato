check_requirements() {
  REQUIREMENTS="filewatcher nosetests coverage"
  for r in $REQUIREMENTS
  do
    hash $r 2>/dev/null || {
      echo >&2 "I require $r but it's not installed. Aborting."
      exit 1;
    }
  done
}

