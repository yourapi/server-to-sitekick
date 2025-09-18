import random
from importlib import import_module
from pathlib import Path
from pprint import pprint


def get_server_modules(root_module='providers', filter=None):
    """Inspect all server modules and see which ones are valid by calling is_server_type(). When the module is valid,
    it is returned."""
    modules = []
    if filter is None:
        filter = lambda module: True
    for filename in Path(__file__).parent.parent.glob(f'{root_module}/*.py'):
        if filename.stem == '__init__':
            continue
        if not filter(filename.stem):
            continue
        try:
            module = import_module(f"{root_module}.{filename.stem}")
            modules.append(module)
        except Exception as e:
            print(f"Error importing module {root_module}.{filename.stem}: {e}")
    return modules

def test_modules(which_modules=None):
    """Test all modules, or the specified modules."""
    if which_modules is None or which_modules == 'latest':
        # No module specified; get the most recently changed module:
        modules = get_server_modules()
        modules.sort(key=lambda module: Path(module.__file__).stat().st_mtime, reverse=True)
        modules = modules[:1]
    elif which_modules == 'all':
        # Get all modules:
        modules = get_server_modules()
    else:
        # Get only the specified module name:
        modules = get_server_modules(filter=lambda module: module in which_modules.split(','))
    # Now the specified modules are loaded, test them:
    for module in modules:
        print(f"=== Testing module {module.__name__} ===")
        if hasattr(module, 'is_server_type') and callable(module.is_server_type):
            try:
                print(f"{module.__name__}.is_server_type(): {module.is_server_type()}")
            except Exception as e:
                print(f"{module.__name__}.is_server_type() error: {e}\nThis server is not supported by this module.")
        else:
            print(f"Error in {module.__name__}: no function is_server_type()")
        try:
            domains = module.get_domains()
            if not isinstance(domains, list):
                print(f"Error in {module.__name__}.get_domains(): returned value is not a list")
            else:
                print(f"Found {len(domains)} domains in {module.__name__}.get_domains()")
                if len(set(domains)) != len(domains):
                    print(f"{module.__name__}.get_domains(): duplicate domains found, {len(domains) - len(set(domains))} duplicates.")
                if domains:
                    # Show a sample of the domains, random 5 sorted domains:
                    domains = sorted(random.sample(list(set(domains)), min(len(set(domains)), 5)))
                    s_domains = ', '.join(domains)
                    print(f"Sample of domains: {s_domains}")
        except Exception as e:
            domains = []
            print(f"Error in {module.__name__}.get_domains(): {e}")
        if not domains:
            print('No domains found; testing empty value')
            domains.append('')
        for domain in domains:
            print(f"Testing '{domain}'...")
            try:
                domain_info = module.get_domain_info(domain)
                print('-' * 80)
                pprint(domain_info, indent=4)
                if not isinstance(domain_info, dict):
                    print(f"{module.__name__}.get_domain_info({domain}) returns no dict but a {type(domain_info)}")
            except Exception as e:
                print(f"Error in {module.__name__}.get_domain_info({domain}): {e}")
