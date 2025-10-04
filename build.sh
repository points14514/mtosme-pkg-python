echo "First, you have to install some libraries"
 
pip install pyyaml
 
pip install requests

pip install distro
 
pip install psutil
 
pip install ujson
 
pip install docker
# If you are rhel, then you can carry out this life
# sudo dnf install python3-dnf
# Or are you termux, If a command is missing, you can install it(For example:ldd)
# pkg install ldd
echo "Then, install the required compilers"
pip install pyinstaller
pyinstaller -F main.py --name mtosme-pkg
echo "Compilation complete, you can use it normally"
mv build/mtosme-pkg ~/../usr/bin
# Or you're not termux. You can also carry out this order
# mv mtosme-pkg /usr/bin
# Remember. Don't put it down /usr/lib, because this is not the directory where the binaries are
sleep 9
exit 1
