from pathlib import Path
from typing import List

import traitlets as T
import yaml
from constructor.conda_interface import cc_platform
from .shell import SHELL


from ..constants import REQUIRED_PKGS, WIN, DEFAULT_ICON
from .conda import (
    add_package_to_lock,
    add_package_to_yaml,
    explicit_url,
    find_env,
    format_local_channel,
    install_many,
    install_one,
    is_installed,
    is_local_channel,
)


class ConstructorSettings(T.HasTraits):
    install_missing: bool = T.Bool(False)
    path: Path | None = T.Instance(Path, allow_none=True, default_value=None)
    environment_yaml: str = T.Unicode()
    explicit_lock: str = T.Unicode()
    install_path: str = T.Unicode()

    name: str = T.Unicode()
    version: str = T.Unicode()
    channels: tuple[str] = T.Tuple()
    specs: tuple[str] = T.Tuple()
    channels_remap: tuple[dict[str, str]] = T.Tuple()
    environment_file: str | None = T.Unicode(None, allow_none=True)
    environment: str | None = T.Unicode(None, allow_none=True)

    company: str | None = T.Unicode(None, allow_none=True)
    license_file: str | None = T.Unicode(None, allow_none=True)
    installer_filename: str | None = T.Unicode(None, allow_none=True)
    header_image_text: str | None = T.Unicode(None, allow_none=True)
    default_image_color: str | None = T.Unicode(None, allow_none=True)
    signing_identity_name: str | None = T.Unicode(None, allow_none=True)
    welcome_image_text: str | None = T.Unicode(None, allow_none=True)
    batch_mode: bool | None = T.Bool(allow_none=True)
    default_prefix: str | None = T.Unicode(None, allow_none=True)
    default_prefix_domain_user: str | None = T.Unicode(None, allow_none=True)
    default_prefix_all_users: str | None = T.Unicode(None, allow_none=True)
    register_python_default: bool = T.Bool(False)
    post_install: str = T.Unicode(None, allow_none=True)
    extra_files: list = T.List(
        default_value=[
            {"Menu/icon.ico": "Menu/icon.ico"},
            {"Menu/widgetron_shortcut.json": "Menu/widgetron_shortcut.json"},
        ]
    )
    icon_image: str | None = T.Unicode(None, allow_none=True)

    # Paths relative to construct.yaml
    nsis_template: str | None = T.Unicode(None, allow_none=True)
    header_image: str | None = T.Unicode(None, allow_none=True)
    welcome_image: str | None = T.Unicode(None, allow_none=True)

    _local_channels: List[str] = T.Tuple()
    _non_local_channels: List[str] = T.Tuple()

    def __init__(self, **kw):
        kw["icon_image"] = kw.get("icon", str(DEFAULT_ICON))
        kw["specs"] = kw.get("dependencies", [])
        super().__init__(**{k: v for k, v in kw.items() if k in self.trait_names()})
        self.observe(self.render, names=self.trait_names())

    @T.validate("channels")
    def _on_channels_changed(self, proposal: T.Bunch) -> None:
        seen = set()
        channels = []
        for c in proposal["value"]:
            if c not in seen:
                seen.add(c)
                channels.append(c)

        self._local_channels = [x for x in channels if is_local_channel(x)]
        self._non_local_channels = [x for x in channels if not is_local_channel(x)] or [
            "conda-forge"
        ]
        channels = [*self._local_channels, *self._non_local_channels]
        # for x in self._local_channels:
        #     validate_local_channel(x)  # Fails on linux
        self.channels_remap = [
            {"src": c, "dest": "https://repo.anaconda.com/pkgs/main"}
            for c in self._local_channels
        ]
        return channels

    def add_local(self, path: Path | str):
        self.channels = (format_local_channel(path), *self.channels)

    @T.observe("specs")
    def _validate_specs(self, e: T.Bunch) -> None:
        if self.specs:
            for pkg, _ in REQUIRED_PKGS:
                assert any(
                    [pkg in x.split() for x in self.specs]
                ), f"Required package ({pkg}) not found in specified specs."

    @T.observe("environment")
    def _validate_environment(self, e: T.Bunch) -> None:
        assert Path(self.environment).exists()
        missing_packages = [
            (p, v) for p, v in REQUIRED_PKGS if not is_installed(self.environment, p)
        ]
        if self.install_missing:
            install_many(Path(self.environment), missing_packages)
        else:
            assert (
                not missing_packages
            ), f"Environment is missing the following required packages ({missing_packages})"

    @T.validate("install_path")
    def _validate_install_path(self, proposal: T.Bunch):
        value = proposal.value
        if WIN:
            value = str(Path(value)).replace("\\\\", "\\")
        #: Set if not explicitly provided
        self.default_prefix = self.default_prefix or value
        self.default_prefix_all_users = self.default_prefix_all_users or value
        self.default_prefix_domain_user = self.default_prefix_domain_user or value
        return value

    @T.validate("environment_file")
    def _on_env_file(self, proposal: T.Bunch) -> None:
        if self.environment_yaml:
            return proposal.value
        if self.explicit_lock:
            return proposal.value
        raise ValueError(
            "You may not set environment_file directly. Use `environment_yaml` or `explicit_lock` instead."
        )

    @T.validate("icon_image")
    def _on_icon_change(self, e: T.Bunch) -> None:
        (self.path / "Menu").mkdir(parents=True, exist_ok=True)
        SHELL.copy(self.icon_image, self.path / "Menu/icon.ico")
        SHELL.copy(self.icon_image, self.path / "icon.ico")
        return "icon.ico"

    @T.validate("post_install")
    def _on_post_install_change(self, e: T.Bunch) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        p = Path(self.post_install)
        SHELL.copy(str(p), self.path / p.name)
        return p.name
    
    @T.validate("extra_files")
    def _on_extra_files(self, proposal: T.Bunch) -> dict:
        new = self.extra_files
        new.update(**proposal.value)
        return new

    @T.observe("environment_yaml")
    def _on_env_yaml(self, e: T.Bunch) -> None:
        # NOTE: It should be possible to build off of the yaml file directly
        #   but was running into issues with local channels not being handled
        #   correctly.
        # TODO: Run conda-lock and give the lockfile to constructor
        data = yaml.safe_load(Path(self.environment_yaml).read_text())
        self.channels = data["channels"]
        self.specs = data["dependencies"]

    @T.observe("explicit_lock")
    def _on_env_lock(self, e: T.Bunch) -> None:
        self.environment_file = str(
            (self.path / Path(self.explicit_lock).name).with_suffix(".txt")
        )
        content = Path(self.explicit_lock).read_text()
        Path(self.environment_file).write_text(content)

        # Check for local channels for channels_remap
        lines = [x.strip() for x in content.strip().split("\n")]
        urls = lines[lines.index("@EXPLICIT") + 1 :]
        channels = []
        for url in urls:
            if url.strip():
                for subdir in ["noarch", cc_platform]:
                    if f"/{subdir}/" in url:
                        channel, package = url.split(f"/{subdir}/")
                        channels.append(channel)
                        break
                else:
                    raise ValueError(f"Unexpected package url. ({url})")
        self.channels = channels

    @T.validate("name")
    def _clean_name(self, proposal: T.Bunch) -> str:
        return "_".join(proposal.value.split())

    def add_dependency(self, package, channel, **package_attrs):
        if is_local_channel(channel):
            channel = format_local_channel(channel)
        self.channels = (*self.channels, channel)
        assert (
            sum(
                [
                    int(bool(x))
                    for x in (
                        self.specs,
                        self.environment_file and self.environment_yaml,
                        self.environment_file and self.explicit_lock,
                        self.environment,
                    )
                ]
            )
            == 1
        ), "Expected only one suitable environment specification. Found multiple. This should never happen. Please report this to https://github.com/JoelStansbury/widgetron/issues"
        if self.specs:
            url = explicit_url(package, channel, **package_attrs)
            self.specs = (*self.specs, url)
            return 0
        if self.environment_file and self.environment_yaml:
            add_package_to_yaml(
                Path(self.environment_file), package, channel, **package_attrs
            )
            return 0
        if self.environment_file and self.explicit_lock:
            add_package_to_lock(
                Path(self.environment_file), package, channel, **package_attrs
            )
            return 0
        if self.environment:
            return install_one(self.environment, package, channel, **package_attrs)
        raise ValueError(
            "No suitable environment specification identified. This should never happen. Please report this to https://github.com/JoelStansbury/widgetron/issues"
        )

    @T.validate("environment")
    def _ensure_directory_exists(self, proposal: T.Bunch):
        return find_env(proposal["value"])

    @T.validate(
        "icon_image",
        "nsis_template",
        "header_image",
        "welcome_image",
        "environment_yaml",
        "explicit_lock",
        "environment_file",
        "license_file",
        "post_install",
    )
    def _ensure_file_exists(self, proposal: T.Bunch):
        p = Path(proposal["value"])
        if not p.exists():
            raise ValueError(f"File not found: {p}")
        if not p.is_file():
            raise ValueError(f"Expected a file, not a directory: {p}")
        return str(p.resolve())

    def render(self, *_):
        if not self.path:
            return
        omit = {
            "path",
            "_local_channels",
            "_non_local_channels",
            "install_missing",
            "path",
            "environment_yaml",
            "explicit_lock",
            "install_path",
        }.union({"channels", "specs"} if self.environment_file else set())
        d = {
            k: v
            for k, v in self.trait_values().items()
            if v not in (None, "", [], tuple()) and k not in omit
        }
        yml = yaml.safe_dump(d)
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "construct.yaml").write_text(yml)

    def validate(self):
        assert (
            self.environment or self.environment_file or (self.specs and self.channels)
        ), "Missing environment specification"
