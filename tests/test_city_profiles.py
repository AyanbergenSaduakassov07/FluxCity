"""Any-city support: the Astana network profile and city-agnostic geometry."""

import geopandas as gpd
from shapely.geometry import box

from sim.common import load_yaml
from sim.network.build_city import PROFILES, _p, netconvert_args
from sim.network.geo import read_poly


def test_astana_profile_paths_are_astana_only():
    cfg = load_yaml(PROFILES["astana"])
    assert cfg["name"] == "astana"
    for key in ("polygon", "clip_pbf", "osm_xml", "fixes_dir", "out_dir", "net"):
        assert "jeddah" not in cfg[key] and "astana" in cfg[key], key
    assert "kazakhstan" in cfg["extract"]["url"]
    assert "--tls.guess-signals" in netconvert_args(cfg)


def test_astana_polygon_covers_the_city_centre():
    poly = read_poly(_p(load_yaml(PROFILES["astana"])["polygon"]))
    baiterek = (71.4304, 51.1283)
    assert poly.contains(gpd.points_from_xy([baiterek[0]], [baiterek[1]])[0])


def test_area_uses_local_utm_zone():
    gdf = gpd.GeoDataFrame(geometry=[box(71.40, 51.10, 71.45, 51.15)], crs="EPSG:4326")
    assert gdf.estimate_utm_crs().to_epsg() == 32642  # Astana is UTM 42N, not Jeddah's 37N
