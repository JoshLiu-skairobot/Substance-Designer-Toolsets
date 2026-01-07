# Substance Automation Toolkit (SAT)

### Default behavior of the SAT API regarding the application install path

**Windows :** SAT will find automatically the path, but the user can overload it with the environment variable `SDAPI_SATPATH`, if the user moves the installation folder elsewhere.

**macOS :** SAT will assume the install path is `/Application/Substance Automation Toolkit`, if the user moves the folder elsewhere the `SDAPI_SATPATH` should be set on the `.bash_profile` file.

**Linux :** SAT will search in `/opt/Allegorithmic/Substance_Automation_Toolkit` folder, but it is up to the user to place the files; so if you are not using the recommended path you need to set the `SDAPI_SATPATH` environment variable on your `.bashrc` file.

### How to set the environment variable for the SAT:

Substance Automation Toolkit requires an environment variable to be set by the user, in the case that the default installation folder is modified. This readme file intends to explain how to do it in a macOS/Linux environment.

### Bash (The default shell on macOS and most Linux distributions)

Setting for the current session:

```bash
$ export SDAPI_SATPATH="/<Installation Folder>"
$ echo $SDAPI_SATPATH
-> "/<Installation Folder>"
```

To persist this, you need to edit the `.bash_profile` file on macOS or your `.bashrc` file on Linux, which is inside your home directory to include the following line:

```
# other stuff
export SDAPI_SATPATH="/This_is/The Path/to the/<Installation Folder>"
```

You then need to make sure your system loads in the new variables. You can do this using the `source` command:

```bash
$ echo $SDAPI_SATPATH
->
$ source ~/.bash_profile
$ echo $SDAPI_SATPATH
-> "/This_is/The Path/to the/<Installation Folder>"
```

for linux use `$ source ~/.bashrc`
