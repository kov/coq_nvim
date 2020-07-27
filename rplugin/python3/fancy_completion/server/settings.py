from inspect import getmembers, isfunction
from math import inf
from os.path import exists, join
from typing import Any, Iterator, Sequence

from ..shared.da import load_json, load_module, merge_all
from ..shared.types import Seed
from .consts import load_hierarchy, module_entry_point, settings_json
from .types import FuzzyOptions, Settings, SourceFactory, SourceSpec


def load_source(config: Any) -> SourceSpec:
    spec = SourceSpec(
        main=config["main"],
        short_name=config["short_name"],
        enabled=config["enabled"],
        limit=config.get("limit"),
        timeout=config.get("timeout"),
        config=config.get("config"),
    )
    return spec


def initial(configs: Sequence[Any]) -> Settings:
    config = merge_all(load_json(settings_json), *configs)
    fuzzy_o = config["fuzzy"]
    fuzzy = FuzzyOptions(min_match=fuzzy_o["min_match"],)
    sources = {name: load_source(conf) for name, conf in config["sources"].items()}
    settings = Settings(fuzzy=fuzzy, sources=sources)
    return settings


def load_factories(settings: Settings) -> Iterator[SourceFactory]:
    for src_name, spec in settings.sources.items():
        for path in load_hierarchy:
            candidate = join(path, spec.main)
            if exists(candidate):
                mod = load_module(candidate)
                for name, func in getmembers(mod, isfunction):
                    if name == module_entry_point:
                        limit = spec.limit or inf
                        timeout = (spec.timeout or inf) / 1000
                        config = spec.config or {}
                        seed = Seed(config=config, limit=limit, timeout=timeout)
                        fact = SourceFactory(
                            name=src_name,
                            short_name=spec.short_name,
                            limit=limit,
                            timeout=timeout,
                            seed=seed,
                            manufacture=func,
                        )
                        yield fact
