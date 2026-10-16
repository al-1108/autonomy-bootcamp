"""
TODO(bootcamper): write the tests for ``src/waypoint_utils.py`` in here.

The example below covers files that parse fine: with and without ``home``,
and files with comments and blank lines in them. The rest is yours:

- ``east_north_coordinate_offset_m``: offsets you worked out yourself,
  compared with ``pytest.approx``. Never use ``==`` on meters.
- Ordering: with no ``home``, ``sort_clockwise_sweep`` goes clockwise
  starting from north.
- With a ``home``: the order starts in home's direction instead, and goes
  back to starting at north if home is right on top of the centroid.
- Parsing gives you frozen ``Coordinate`` objects that can't be changed.
- Out of range: latitudes past +/-90 and longitudes past +/-180 get
  rejected.
- Nothing to work with: an empty file, an empty ``waypoints`` list, and
  ``sort_clockwise_sweep`` given a list of 0 or 1 waypoints.
- Bad data: a file whose top level isn't a mapping, waypoints missing
``lat``, ``lon``, or ``alt``, values that aren't numbers, YAML that
doesn't parse, and a file that isn't there.
- Two waypoints in the same direction: the closer one comes first.

Graded by ``warg run utils grade-tests``: pass on the real code, 90% branch
coverage, and fail on every broken copy in ``grader/mutants/``.
"""

import math

import pytest

from src.constants import EARTH_RADIUS_M, TWO_PI
from src.types import Coordinate
from src.waypoint_utils import (
    east_north_coordinate_offset_m,
    parse_waypoints_file,
    sort_clockwise_sweep,
)

# The helper and the test below are given to you.

def write_to_tmp_waypoints_file(tmp_path, text):
    """Write ``text`` to a YAML file and hand back its path.

    ``tmp_path`` is a pytest fixture: a fresh empty directory per test.
    """
    path = tmp_path / "waypoints.yaml"
    path.write_text(text)
    return path


# One test, three files. ``parametrize`` runs the test body once per
# ``(text, expected)`` pair, and ``ids`` names each run so a failure tells you
# which file broke.
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            """
            home: {lat: 1, lon: 2, alt: 3}
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
        (
            """
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
              - {lat: 7, lon: 8, alt: 9}
            """,
            (None, [Coordinate(4, 5, 6), Coordinate(7, 8, 9)]),
        ),
        (
            """
            # a lap

            home: {lat: 1, lon: 2, alt: 3}

            waypoints:
              # first leg
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
    ],
    ids=["home-and-waypoints", "no-home", "comments-and-blank-lines"],
)
def test_parse_waypoints_file_success(tmp_path, text, expected):
    path = write_to_tmp_waypoints_file(tmp_path, text)
    assert parse_waypoints_file(path) == expected


def test_placeholder():
    # TODO(bootcamper): delete this and write real tests. It's only here so
    # linter doesn't complain about unused imports before you start.
    assert callable(east_north_coordinate_offset_m)
    assert callable(parse_waypoints_file)
    assert callable(sort_clockwise_sweep)

def test_empty_file(tmp_path):
    path = write_to_tmp_waypoints_file(tmp_path, "")
    res = parse_waypoints_file(path)
    assert res == (None, [])

def test_sort_no_waypoints(tmp_path):
    assert sort_clockwise_sweep([]) == []

def test_sort_one_waypoint(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path, 
        """
        waypoints:
          - {lat: 1, lon: 1, alt: 1}
        """)
    waypoints = parse_waypoints_file(path)[1]
    assert sort_clockwise_sweep(waypoints) == waypoints

def test_out_of_range(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 91, lon: 0, alt: 0}
        """)
    with pytest.raises(ValueError):
        parse_waypoints_file(path)
    
def test_bad_data(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: hello, lon: 2, alt: 3}
        """)
    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_missing_data(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lat: 2, lon: 2}
        """)
    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_not_mapping(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        - {lat: 1, lon: 2, alt: 3}
        - {lat: 4, lon: 5, alt: 6}
        """)
    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_invalid_yaml(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        """
        waypoints:
          - {lon: 2, alt: 3
        """)
    with pytest.raises(ValueError):
        parse_waypoints_file(path)

def test_missing_file():
    with pytest.raises(OSError):
      parse_waypoints_file("ueshushf.yaml")

def test_two_waypoints_same_dir():
    near = Coordinate(lat=1, lon=0, alt=0)
    far = Coordinate(lat=2, lon=0, alt=0)
    south = Coordinate(lat=-3, lon=0, alt=0)

    waypoints = [far, south, near]
    result = sort_clockwise_sweep(waypoints)
    assert result == [near, far, south]

def test_zero_offset():
    east, north = east_north_coordinate_offset_m(0, 0, 0, 0)
    assert north == pytest.approx(0, abs=1e-6)
    assert east == pytest.approx(0, abs=1e-6)

def test_north_offset():
    east, north = east_north_coordinate_offset_m(0, 0, 5, 0)
    assert east == pytest.approx(0, abs=1e-6)
    assert north == pytest.approx(5*EARTH_RADIUS_M*math.pi/180, abs=1e-6)

def test_east_offset_with_lat():
    east, north = east_north_coordinate_offset_m(60, 0, 60, 1)
    assert east == pytest.approx(TWO_PI*EARTH_RADIUS_M/360*0.5, abs=1e-6)
    assert north == pytest.approx(0, abs=1e-6)

def test_sort_with_home():
    north = Coordinate(lat=1, lon=0, alt=0)
    east = Coordinate(lat=0, lon=1, alt=0)
    south = Coordinate(lat=-1, lon=0, alt=0)
    west = Coordinate(lat=0, lon=-1, alt=0)

    res = sort_clockwise_sweep([north, east, west, south], Coordinate(lat=0, lon=0.5, alt=0))
    assert res == [east, south, west, north]