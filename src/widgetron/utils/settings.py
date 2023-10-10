from pathlib import Path
from typing import List

import constructor
import traitlets as T
import yaml

from widgetron.utils.shell import SHELL

from ..constants import REQUIRED_PKGS, TEMP_DIR, WIN
from .conda import (
    add_package_to_lock,
    add_package_to_yaml,
    ensure_not_installed,
    explicit_url,
    find_env,
    format_local_channel,
    install_many,
    install_one,
    is_installed,
    is_local_channel,
    is_lock_file,
    validate_local_channel,
)


class ConstructorSettings(T.HasTraits):
    install_missing: bool = T.Bool(False)
    path: Path = TEMP_DIR / "constructor"
    environment_yaml: str = T.Unicode()
    explicit_lock: str = T.Unicode()
    install_path: str = T.Unicode()

    name: str = T.Unicode()
    version: str = T.Unicode()
    channels: tuple[str] = T.Tuple(["https://conda.anaconda.org/conda-forge"])
    specs: tuple[str] = T.Tuple()
    channels_remap: tuple[dict[str, str]] = T.Tuple()
    environment_file: str | None = T.Unicode(None, allow_none=True)
    environment: str | None = T.Unicode(None, allow_none=True)

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
    post_install: str = T.Unicode("post_install.sh  # [not win]")
    icon_image: str | None = T.Unicode(None, allow_none=True)

    # Paths relative to construct.yaml
    nsis_template: str | None = T.Unicode(None, allow_none=True)
    header_image: str | None = T.Unicode(None, allow_none=True)
    welcome_image: str | None = T.Unicode(None, allow_none=True)

    _local_channels: List[str] = T.Tuple()
    _non_local_channels: List[str] = T.Tuple()

    def __init__(self, **kw):
        if "icon" in kw:
            kw["icon_image"] = kw["icon"]
        kw["specs"] = kw.get("dependencies", [])
        self.path.mkdir(parents=True, exist_ok=True)
        super().__init__(**{k: v for k, v in kw.items() if k in self.trait_names()})
        self.render()
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
        for x in self._local_channels:
            validate_local_channel(x)
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
            value = "\\".join(Path(value).parts)
        #: Set if not explicitly provided
        self.default_prefix = self.default_prefix or value
        self.default_prefix_all_users = self.default_prefix_all_users or value
        self.default_prefix_domain_user = self.default_prefix_domain_user or value
        return value

    @T.validate("environment_file")
    def _on_env_file(self, proposal: T.Bunch) -> None:
        if self.environment_yaml:
            assert (
                Path(proposal.value).name == Path(self.environment_yaml).name
            ), "Conflicting spec files (you may only have one)"
            SHELL.copy(self.environment_yaml, proposal.value)
            return proposal.value
        if self.explicit_lock:
            assert (
                Path(proposal.value).name == Path(self.explicit_lock).name
            ), "Conflicting spec files (you may only have one)"
            SHELL.copy(self.explicit_lock, proposal.value)
            return proposal.value
        raise ValueError(
            "You may not set environment_file directly. Use `environment_yaml` or `explicit_lock` instead."
        )

    @T.observe("environment_yaml")
    def _on_env_yaml(self, e: T.Bunch) -> None:
        # data = yaml.safe_load(Path(self.environment_yaml).read_text())
        # self.channels = data["channels"]
        # self.specs = data["dependencies"]

        env_cp = self.path / Path(self.environment_yaml).name
        env_cp.write_text(Path(self.environment_yaml).read_text())
        self.environment_file = str(env_cp.absolute())

    @T.observe("explicit_lock")
    def _on_env_lock(self, e: T.Bunch) -> None:
        assert constructor.__version__ >= "3.4.5", (
            "Support for explicit lockfiles was added in constructor=3.4.5. "
            f"You have constructor={constructor.__version__}"
        )
        assert is_lock_file(self.explicit_lock), "Not a valid lock file."
        self.environment_file = str(self.path / Path(self.explicit_lock).name)

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
            rc = ensure_not_installed(self.environment, package)
            return rc or install_one(
                self.environment, package, channel, **package_attrs
            )
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
    )
    def _ensure_file_exists(self, proposal: T.Bunch):
        p = Path(proposal["value"])
        assert p.exists()
        assert p.is_file()
        return str(p.absolute())

    def render(self, *_):
        omit = {
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
