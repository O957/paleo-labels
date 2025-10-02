"""Measurement conversion utilities for paleo-labels."""

POINTS_PER_INCH = 72
INCHES_TO_CM = 2.54
CM_TO_INCHES = 1 / INCHES_TO_CM
POINTS_PER_CM = POINTS_PER_INCH * CM_TO_INCHES


def inches_to_points(inches: float) -> float:
    """Convert inches to points (1/72 inch).

    Parameters
    ----------
    inches : float
        Value in inches to convert.

    Returns
    -------
    float
        Value converted to points.
    """
    return inches * POINTS_PER_INCH


def cm_to_points(cm: float) -> float:
    """Convert centimeters to points.

    Parameters
    ----------
    cm : float
        Value in centimeters to convert.

    Returns
    -------
    float
        Value converted to points.
    """
    return cm * POINTS_PER_CM


def points_to_inches(points: float) -> float:
    """Convert points to inches.

    Parameters
    ----------
    points : float
        Value in points to convert.

    Returns
    -------
    float
        Value converted to inches.
    """
    return points / POINTS_PER_INCH


def points_to_cm(points: float) -> float:
    """Convert points to centimeters.

    Parameters
    ----------
    points : float
        Value in points to convert.

    Returns
    -------
    float
        Value converted to centimeters.
    """
    return points / POINTS_PER_CM
