Development
==============

## Steps to run tests

### Install pyenv

```
brew update
brew install pyenv
```

### Add required versions

```
pyenv install 3.3.6
pyenv install 3.4.5
pyenv install pypy-5.3.1
```

### Add the following lines to bashrc

```
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

### Add the versions globally

```
pyenv global system 3.4.5
pyenv global system 3.3.6
pyenv global system pypy-5.3.1
```
