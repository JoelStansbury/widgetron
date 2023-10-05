from pathlib import Path
from typing import List
import traitlets as T
import yaml

import constructor

from ..constants import DEFAULT_ICON, REQUIRED_PKGS, TEMP_DIR
from .conda import is_lock_file, is_installed, install, is_local_channel, validate_local_channel, format_local_channel, add_package



class Shared(T.HasTraits):
    name: str = T.Unicode("Widgetron")
    name_nospace: str = "Widgetron"
    icon: Path = DEFAULT_ICON
    license_file: str | None = T.Unicode()
    company: str | None = T.Unicode()

    @T.observe("name")
    def _on_name_changed(self, e:T.Bunch):
        self.name_nospace = "_".join(self.name.split())



class ConstructorSettings(T.HasTraits):
    install_missing: bool = T.Bool(False)

    name: str = T.Unicode()
    version: str = T.Unicode()
    channels: tuple[str] = T.Tuple(["conda-forge"])
    dependencies: tuple[str] = T.Tuple()
    channels_remap: tuple[dict[str, str]] = T.Tuple()
    environment_file: str | None = T.Unicode(None, allow_none=True)

    installer_filename: str | None = T.Unicode(None, allow_none=True)
    header_image_text: str | None = T.Unicode(None, allow_none=True)
    default_image_color: str | None = T.Unicode(None, allow_none=True)
    signing_identity_name: str | None = T.Unicode(None, allow_none=True)
    welcome_image_text: str | None = T.Unicode(None, allow_none=True)
    batch_mode: bool | None = T.Bool(allow_none=True)
    default_prefix: str | None = T.Unicode(None, allow_none=True)
    default_prefix_domain_user: str | None = T.Unicode(None, allow_none=True)
    default_prefix_all_users: str | None = T.Unicode(None, allow_none=True)

    # Paths relative to construct.yaml
    environment: str | None = T.Unicode(None, allow_none=True)
    nsis_template: str | None = T.Unicode(None, allow_none=True)
    header_image: str | None = T.Unicode(None, allow_none=True)
    welcome_image: str | None = T.Unicode(None, allow_none=True)

    _local_channels: List[str] = T.Tuple()
    _non_local_channels: List[str] = T.Tuple()

    def __init__(self, **kw):
        super().__init__(**{k: v for k, v in kw.items() if hasattr(self, k)})

    @T.validate("channels")
    def _on_channels_changed(self, proposal:T.Bunch) -> None:
        seen = set()
        channels = []
        for c in proposal["value"]:
            if c not in seen:
                seen.add(c)
                channels.append(c)
        
        self._local_channels = [x for x in channels if is_local_channel(x)]
        self._non_local_channels = [x for x in channels if not is_local_channel(x)]
        channels = [*self._local_channels, *self._non_local_channels]
        # for x in self._local_channels:
        #     validate_local_channel(x)
        self.channels_remap = [{"src":c, "dest": self._non_local_channels[0]} for c in self._local_channels]
        return channels

    def add_local(self, path: Path | str):
        self.channels = (format_local_channel(path), *self.channels)

    @T.observe("dependencies")
    def _validate_dependencies(self, e:T.Bunch) -> None:
        for pkg, _ in REQUIRED_PKGS:
            assert any([pkg in x.split() for x in self.dependencies]), f"Required package ({pkg}) not found in specified dependencies."
    
    @T.observe("environment")
    def _validate_environment(self, e:T.Bunch) -> None:
        assert Path(self.environment).exists()
        missing_packages = [(p,v) for p,v in REQUIRED_PKGS if not is_installed(self.environment, p)]
        if self.install_missing:
            install(missing_packages)
        else:
            assert not missing_packages, f"Environment is missing the following required packages ({missing_packages})"
 
    @T.validate("environment_file")
    def _on_env_yaml(self, proposal:T.Bunch) -> None:
        filename = Path(proposal["value"])
        spec = filename.read_text()
        
        if is_lock_file(content=spec):
            assert constructor.__version__ >= "3.4.5", f"Support for explicit lockfiles was added in constructor=3.4.5. You have constructor={constructor.__version__}"

        new_path = TEMP_DIR / "constructor" / filename.name
        new_path.write_text(spec)
        return str(new_path)

    def add_dependency(self, package, channel, **package_attrs):
        if is_local_channel(channel):
            channel = format_local_channel(channel)
        if channel not in self.channels:
            self.channels = (*self.channels, channel)
        if self.environment_file:
            f = Path(self.environment_file)
            f.write_text(add_package(f.read_text, package, channel))
            return
        if "version" in package_attrs:
            package = f"{package} ={package_attrs['version']}"
        self.dependencies = (*self.dependencies, package)

    @T.validate("nsis_template", "header_image", "welcome_image", "environment")
    def _make_absolute(self, proposal:T.Bunch):
        p = Path(proposal["value"])
        assert p.exists()
        return str(p.absolute())

    def to_yaml(self):
        omit = {"_local_channels", "_non_local_channels", "install_missing"}
        d = {k:v for k,v in self.trait_values().items() if v and k not in omit}
        return yaml.safe_dump(d)


class ElectronSettings(T.HasTraits):
    url_whitelist: list[str] = []
    domain_whitelist: list[str] = []

    
class ServerSettings(T.HasTraits):
    filename: Path
    server_command: list[str] = ["jupyter", "lab", "--no-browser"]
    server_executable: list[str] = []
    server_command_args: list[str]