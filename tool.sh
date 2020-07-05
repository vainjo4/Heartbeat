#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo ""
  echo "Please specify a task: "
  echo "  setup: setups a virtualenv needed for the other commands"
  echo "  build: builds binary wheels of both components"
  echo "  test: runs tests"
  echo "  style-analysis: runs static style analysis"
  echo "  install_agent: installs heartbeat_agent to local venv"
  echo "  install_exporter: installs heartbeat_exporter to local venv"  
  echo ""
fi

TASK=$1

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

PYTHON=python3
PIP=pip3

echo "Script running at $SCRIPT_DIR"

if [ "$TASK" == 'setup' ] || [ ! -d test/venv ]; then
  echo "Setup a virtualenv at $SCRIPT_DIR/test/venv"
  cd test
  $PYTHON -m venv venv
  source venv/bin/activate
  $PIP install -r requirements.txt
  cd ..
  if [ "$TASK" == 'setup' ]; then
    exit 0
  fi
else
  source test/venv/bin/activate
  echo "Using the virtualenv at $SCRIPT_DIR/test/venv"
fi

if [ "$TASK" == 'build' ]; then

  cd heartbeat_exporter
  $PYTHON setup.py bdist_wheel
  cd ..

  cd heartbeat_agent
  $PYTHON setup.py bdist_wheel
  cd ..

  AGENT_PATH=$(ls "$SCRIPT_DIR"/heartbeat_agent/dist/*whl)
  EXPORTER_PATH=$(ls "$SCRIPT_DIR"/heartbeat_exporter/dist/*whl)

  echo ""
  echo "Build done, wheels can be found at"
  echo "  $AGENT_PATH"
  echo "  $EXPORTER_PATH"
  echo ""
fi

if [ "$TASK" == 'test' ]; then
  REPORT_PATH="test/reports/heartbeat-test-report.xml"
  mkdir -p test/reports
  rm -f "$REPORT_PATH"
  pytest --junitxml="$REPORT_PATH"
  echo ""
  echo "Pytest report is found at $REPORT_PATH"
  echo ""
fi

if [ "$TASK" == 'style-analysis' ]; then
  REPORT_PATH="test/reports/heartbeat-flake8-report.txt"
  mkdir -p test/reports
  rm -f "$REPORT_PATH"
  flake8 . --output-file="$REPORT_PATH" --exclude=".git,__pycache__,*.egg,*_cache,*/venv/*,*/build/*,*/dist/*"
  echo ""
  echo "Flake8 report is found at $REPORT_PATH"
  echo ""
fi

if [ "$TASK" == 'install_agent' ]; then
  AGENT_PATH=$(ls "$SCRIPT_DIR"/heartbeat_agent/dist/*whl)
  $PIP install "$AGENT_PATH"
  echo ""
  echo "Install agent locally: Done"
  echo ""
fi

if [ "$TASK" == 'install_exporter' ]; then
  EXPORTER_PATH=$(ls "$SCRIPT_DIR"/heartbeat_exporter/dist/*whl)
  $PIP install "$EXPORTER_PATH"
  echo ""
  echo "Install exporter locally: Done"
  echo ""
fi


