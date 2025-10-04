#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from abc import ABC, abstractmethod
import yaml
import json

class PackageManagerError(Exception):
    """包管理器基础异常"""
    pass

class UnsupportedDistributionError(PackageManagerError):
    """不支持的Linux发行版"""
    pass

class PackageNotFoundError(PackageManagerError):
    """包未找到"""
    pass

class DependencyError(PackageManagerError):
    """依赖问题"""
    pass

class TransactionError(PackageManagerError):
    """事务执行失败"""
    pass

class OSUtils:
    """操作系统工具类"""
    @staticmethod
    def get_distro():
        """返回当前Linux发行版信息"""
        try:
            with open('/etc/os-release') as f:
                os_release = {}
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os_release[key] = value.strip('"')
                return os_release
        except FileNotFoundError:
            return None
    
    @classmethod
    def is_debian_based(cls):
        distro = cls.get_distro()
        return distro and ('debian' in distro.get('ID', '').lower() or 
                          'ubuntu' in distro.get('ID', '').lower())
    
    @classmethod
    def is_redhat_based(cls):
        distro = cls.get_distro()
        return distro and ('rhel' in distro.get('ID', '').lower() or 
                          'centos' in distro.get('ID', '').lower() or
                          'fedora' in distro.get('ID', '').lower())
    
    @classmethod
    def is_arch_based(cls):
        distro = cls.get_distro()
        return distro and 'arch' in distro.get('ID', '').lower()
    
    @classmethod
    def is_gentoo_based(cls):
        distro = cls.get_distro()
        return distro and 'gentoo' in distro.get('ID', '').lower()
    
    @staticmethod
    def is_admin():
        """检查当前是否是root/admin权限"""
        try:
            return os.getuid() == 0
        except AttributeError:
            return False

    @staticmethod
    def check_admin_or_exit():
        if not OSUtils.is_admin():
            print("错误: 需要管理员权限运行此操作")
            sys.exit(1)

class PackageManagerBackend(ABC):
    """包管理器后端抽象基类"""
    @abstractmethod
    def install(self, package, version=None):
        pass
    
    @abstractmethod
    def remove(self, package):
        pass
    
    @abstractmethod
    def update(self):
        pass
    
    @abstractmethod
    def upgrade(self):
        pass
    
    @abstractmethod
    def search(self, package):
        pass
    
    @abstractmethod
    def list_installed(self):
        pass

class APTBackend(PackageManagerBackend):
    """APT包管理器后端"""
    def install(self, package, version=None):
        cmd = ['sudo', 'apt', 'install', '-y']
        if version:
            cmd.append(f"{package}={version}")
        else:
            cmd.append(package)
        return subprocess.run(cmd, check=True)
    
    def remove(self, package):
        cmd = ['sudo', 'apt', 'remove', '-y', package]
        return subprocess.run(cmd, check=True)
    
    def update(self):
        cmd = ['sudo', 'apt', 'update']
        return subprocess.run(cmd, check=True)
    
    def upgrade(self):
        cmd = ['sudo', 'apt', 'upgrade', '-y']
        return subprocess.run(cmd, check=True)
    
    def search(self, package):
        cmd = ['apt-cache', 'search', package]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    def list_installed(self):
        cmd = ['dpkg', '--list']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

class DNFBackend(PackageManagerBackend):
    """DNF/YUM包管理器后端"""
    def install(self, package, version=None):
        cmd = ['sudo', 'dnf', 'install', '-y']
        if version:
            cmd.append(f"{package}-{version}")
        else:
            cmd.append(package)
        return subprocess.run(cmd, check=True)
    
    def remove(self, package):
        cmd = ['sudo', 'dnf', 'remove', '-y', package]
        return subprocess.run(cmd, check=True)
    
    def update(self):
        cmd = ['sudo', 'dnf', 'check-update']
        return subprocess.run(cmd, check=True)
    
    def upgrade(self):
        cmd = ['sudo', 'dnf', 'upgrade', '-y']
        return subprocess.run(cmd, check=True)
    
    def search(self, package):
        cmd = ['dnf', 'search', package]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    def list_installed(self):
        cmd = ['rpm', '-qa']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

class PacmanBackend(PackageManagerBackend):
    """Pacman包管理器后端"""
    def install(self, package, version=None):
        cmd = ['sudo', 'pacman', '-S', '--noconfirm']
        if version:
            cmd.append(f"{package}-{version}")
        else:
            cmd.append(package)
        return subprocess.run(cmd, check=True)
    
    def remove(self, package):
        cmd = ['sudo', 'pacman', '-R', '--noconfirm', package]
        return subprocess.run(cmd, check=True)
    
    def update(self):
        cmd = ['sudo', 'pacman', '-Sy']
        return subprocess.run(cmd, check=True)
    
    def upgrade(self):
        cmd = ['sudo', 'pacman', '-Su', '--noconfirm']
        return subprocess.run(cmd, check=True)
    
    def search(self, package):
        cmd = ['pacman', '-Ss', package]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    def list_installed(self):
        cmd = ['pacman', '-Q']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

class PackageManager:
    """统一包管理器接口"""
    def __init__(self):
        self.os_utils = OSUtils()
        self.backend = self._get_backend()
        self.dependency_resolver = DependencyResolver(self)
    
    def _get_backend(self):
        """根据系统类型返回对应的包管理器后端"""
        if self.os_utils.is_debian_based():
            return APTBackend()
        elif self.os_utils.is_redhat_based():
            return DNFBackend()
        elif self.os_utils.is_arch_based():
            return PacmanBackend()
        else:
            raise UnsupportedDistributionError("不支持的Linux发行版")
    
    def install(self, package, version=None):
        """安装软件包"""
        OSUtils.check_admin_or_exit()
        return self.backend.install(package, version)
    
    def remove(self, package):
        """卸载软件包"""
        OSUtils.check_admin_or_exit()
        return self.backend.remove(package)
    
    def update(self):
        """更新软件包列表"""
        OSUtils.check_admin_or_exit()
        return self.backend.update()
    
    def upgrade(self):
        """升级所有软件包"""
        OSUtils.check_admin_or_exit()
        return self.backend.upgrade()
    
    def search(self, package):
        """搜索软件包"""
        return self.backend.search(package)
    
    def list_installed(self):
        """列出已安装的软件包"""
        return self.backend.list_installed()
    
    def batch_install(self, config_file):
        """根据配置文件批量安装软件包"""
        OSUtils.check_admin_or_exit()
        config = ConfigLoader.load(config_file)
        for pkg in config.get('packages', []):
            self.install(pkg.get('name'), pkg.get('version'))

class DependencyResolver:
    """依赖关系解析器"""
    def __init__(self, package_manager):
        self.pm = package_manager
    
    def resolve(self, package):
        """解析包的依赖关系"""
        if isinstance(self.pm.backend, APTBackend):
            return self._resolve_apt(package)
        elif isinstance(self.pm.backend, DNFBackend):
            return self._resolve_dnf(package)
        elif isinstance(self.pm.backend, PacmanBackend):
            return self._resolve_pacman(package)
    
    def _resolve_apt(self, package):
        cmd = ['apt-cache', 'depends', package]
        result = subprocess.run(cmd, capture_output=True, text=True)
        dependencies = []
        for line in result.stdout.split('\n'):
            if '依赖:' in line:
                dep = line.split('依赖:')[1].strip()
                if dep not in dependencies:
                    dependencies.append(dep)
        return dependencies
    
    def _resolve_dnf(self, package):
        cmd = ['dnf', 'repoquery', '--requires', package]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.splitlines()
    
    def _resolve_pacman(self, package):
        cmd = ['pactree', package]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.splitlines()

class Transaction:
    """包管理事务"""
    def __init__(self, package_manager):
        self.pm = package_manager
        self.actions = []
    
    def add_install(self, package, version=None):
        self.actions.append(('install', package, version))
    
    def add_remove(self, package):
        self.actions.append(('remove', package))
    
    def commit(self):
        """执行事务中的所有操作"""
        failed_actions = []
        for action in self.actions:
            try:
                if action[0] == 'install':
                    self.pm.install(action[1], action[2](@ref)
                elif action[0] == 'remove':
                    self.pm.remove(action[1](@ref)
            except Exception as e:
                failed_actions.append((action, str(e)))
                self.rollback()
                raise TransactionError(f"事务执行失败: {failed_actions}")
    
    def rollback(self):
        """回滚已执行的操作"""
        # TODO: 实现回滚逻辑
        pass

class ConfigLoader:
    """配置文件加载器"""
    @staticmethod
    def load(file_path):
        """加载配置文件"""
        with open(file_path) as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                return yaml.safe_load(f)
            elif file_path.endswith('.json'):
                return json.load(f)
            else:
                raise ValueError("不支持的配置文件格式")

def main():
    """主函数"""
    pm = PackageManager()
    
    # 示例：安装软件包
    pm.install("nginx")
    
    # 示例：批量安装
    pm.batch_install("packages.yaml")
    
    # 示例：使用事务
    tx = Transaction(pm)
    tx.add_install("git")
    tx.add_install("docker")
    tx.add_remove("apache2")
    tx.commit()

if __name__ == "__main__":
    main()
