#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo ""
  echo "Please specify a task: "
  echo "  setup: setups a virtualenv needed for the other commands"
  echo "  build: builds binary wheels of both components"
  echo "  test: runs tests"
  echo "  install_agent: installs heartbeat_agent to local venv"
  echo "  install_exporter: installs heartbeat_exporter to local venv"  
  echo ""
fi

TASK=$1

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

PYTHON=python3
PIP=pip3

echo $SCRIPT_DIR

if [ "$TASK" == 'setup' ] || [ ! -d test/venv ]; then
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
fi

if [ "$TASK" == 'build' ]; then

  cd heartbeat_exporter
  $PYTHON setup.py bdist_wheel
  cd ..

  cd heartbeat_agent
  $PYTHON setup.py bdist_wheel
  cd ..

  echo ""
  echo "Wheels can be found in"
  echo "  $SCRIPT_DIR/heartbeat_agent/dist"
  echo "  $SCRIPT_DIR/heartbeat_exporter/dist"
  echo ""
fi

if [ "$TASK" == 'test' ]; then
  mkdir -p test/reports
  pytest --junitxml=test/reports/heartbeat-test-report.xml
fi

if [ "$TASK" == 'style-analysis' ]; then
  # integrate flake8
  echo "TODO: unimplemented"
fi

if [ "$TASK" == 'install_agent' ]; then 
  $PIP install heartbeat_agent/dist/heartbeat_agent-0.1-py3-none-any.whl
fi

if [ "$TASK" == 'install_exporter' ]; then
  $PIP install heartbeat_exporter/dist/heartbeat_exporter-0.1-py3-none-any.whl
fi
