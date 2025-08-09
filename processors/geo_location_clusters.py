from typing import Any, Dict, List, Optional, Tuple
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


def _extract_latlon(m: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Extract (lat, lon) from Telegram message dict."""
    loc = m.get("location_information")
    if not isinstance(loc, dict):
        return None
    lat = loc.get("latitude")
    lon = loc.get("longitude")
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return (lat, lon)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great‑circle distance between two lat/lon points in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


class _DSU:
    """Disjoint Set Union (union‑find) for dependency‑free radius clustering (single‑link)."""

    def __init__(self, n: int):
        self.p = list(range(n))
        self.r = [0] * n

    def find(self, x: int) -> int:
        if self.p[x] != x:
            self.p[x] = self.find(self.p[x])
        return self.p[x]

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.r[ra] < self.r[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        if self.r[ra] == self.r[rb]:
            self.r[ra] += 1


def _cluster_labels(coords_df: pd.DataFrame, radius_km: float) -> Tuple[np.ndarray, str]:
    """
    Return (labels, method_used).
    Prefer scikit‑learn DBSCAN(haversine); fallback to union‑find if sklearn is unavailable.
    """
    # Try scikit‑learn DBSCAN
    try:
        from sklearn.cluster import DBSCAN  # type: ignore

        coords_rad = np.radians(coords_df[["lat", "lon"]].values)
        eps_rad = radius_km / 6371.0
        clustering = DBSCAN(eps=eps_rad, min_samples=1, metric="haversine")
        labels = clustering.fit_predict(coords_rad)
        return labels, "scikit-learn DBSCAN (haversine)"
    except Exception:
        # Fallback: union‑find single‑link within radius (O(n^2))
        n = len(coords_df)
        dsu = _DSU(n)
        lats = coords_df["lat"].to_numpy()
        lons = coords_df["lon"].to_numpy()

        # Degree windows tuned to radius: ~1° lat ≈ 111 km
        # Use a 1.8x safety factor to avoid false negatives on coarse check.
        lat_win = max(0.005, 1.8 * (radius_km / 111.0))  # e.g., 2 km -> ~0.0324°
        for i in range(n):
            li, loi = lats[i], lons[i]
            # cos(lat) for longitude scaling; guard against poles
            cos_lat = max(0.1, math.cos(math.radians(li)))
            lon_win = lat_win / cos_lat
            for j in range(i + 1, n):
                lj, loj = lats[j], lons[j]
                if abs(li - lj) > lat_win:
                    continue
                if abs(loi - loj) > lon_win:
                    continue
                if _haversine_km(li, loi, lj, loj) <= radius_km:
                    dsu.union(i, j)

        roots = [dsu.find(i) for i in range(n)]
        root_to_label: Dict[int, int] = {}
        next_label = 0
        labels = np.empty(n, dtype=int)
        for i, r in enumerate(roots):
            if r not in root_to_label:
                root_to_label[r] = next_label
                next_label += 1
            labels[i] = root_to_label[r]
        return labels, "union-find single-link (no sklearn)"


def _render_table_image(df: pd.DataFrame, title: str, out_path) -> None:
    """
    Render a dataframe as a PNG table using Matplotlib.
    """
    n_rows, n_cols = df.shape
    fig_h = max(1.8, 0.35 * (n_rows + 2))
    fig_w = max(6.0, 2.0 * n_cols)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    ax.axis("off")

    ax.set_title(title, fontsize=13, pad=6)

    tbl = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="upper center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.15)

    fig.subplots_adjust(top=0.82)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


@register("geo_location_clusters")
class GeoLocationClusters(BaseProcessor):
    """
    Cluster message locations within a given radius (km) and export:
      1) CSV with cluster center and message count
      2) PNG image of the table (for embedding into reports)

    Kwargs:
      radius_km: float = 2                       # <-- default 2 km
      top_n: int = 50
      decimals: int = 5
      csv_name: str = "geo_location_clusters.csv"
      png_name: str = "geo_location_clusters.png"
      chat_name: str = ""
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        radius_km: float = float(kwargs.get("radius_km", 2))  # default 2 km
        top_n: int = int(kwargs.get("top_n", 50))
        decimals: int = int(kwargs.get("decimals", 5))
        csv_name: str = kwargs.get("csv_name", "geo_location_clusters.csv")
        png_name: str = kwargs.get("png_name", "geo_location_clusters.png")
        chat_name: str = kwargs.get("chat_name", "")

        # Collect coordinates
        coords: List[Tuple[float, float]] = []
        for m in messages:
            pair = _extract_latlon(m)
            if pair:
                coords.append(pair)
        if not coords:
            return

        df = pd.DataFrame(coords, columns=["lat", "lon"])

        # Labels + method
        labels, method = _cluster_labels(df, radius_km)
        df["cluster"] = labels

        # Aggregate clusters
        clusters = (
            df.groupby("cluster")
            .agg(
                count=("lat", "size"),
                center_lat=("lat", "mean"),
                center_lon=("lon", "mean"),
            )
            .reset_index(drop=True)
            .sort_values("count", ascending=False)
        )

        # Round centers for neat display
        clusters["center_lat"] = clusters["center_lat"].round(decimals)
        clusters["center_lon"] = clusters["center_lon"].round(decimals)

        # Build a compact table for PNG (top-N) and clean types
        table_df = clusters.head(top_n).copy()
        table_df.insert(0, "#", range(1, len(table_df) + 1))
        table_df["#"] = table_df["#"].astype(int)
        table_df["count"] = table_df["count"].astype(int)
        fmt = f"{{:.{decimals}f}}"
        table_df["center_lat"] = table_df["center_lat"].map(lambda v: fmt.format(v))
        table_df["center_lon"] = table_df["center_lon"].map(lambda v: fmt.format(v))

        title = f"Geo clusters within {radius_km:.0f} km — {chat_name} ({method})".strip()
        _render_table_image(table_df, title, self.output_dir / png_name)
