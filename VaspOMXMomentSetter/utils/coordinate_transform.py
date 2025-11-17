import numpy as np

def cartesian_to_spherical(s):
    """
    Converts a Cartesian vector [sx, sy, sz] to Spherical coordinates [r, theta, phi].
    Args:
        s (list or np.ndarray): A list or array containing the Cartesian coordinates [sx, sy, sz].
    Returns:
        list: A list containing the Spherical coordinates [r, theta, phi] in radians.
    """
    sx, sy, sz = s
    # Calculate the radius (r)
    r = np.sqrt(sx**2 + sy**2 + sz**2)
    # Handle the case of the vector being at the origin to avoid division by zero
    if r == 0:
        return [0, 0, 0]
    # polar angle (theta) from the positive z-axis, range [0, pi]
    theta = np.arccos(sz / r)
    # azimuthal angle (phi) in the xy-plane from the positive x-axis, range [-pi, pi]
    phi = np.arctan2(sy, sx)

    grad2deg = 180.0/np.pi
    theta *= grad2deg 
    phi *= grad2deg 

    return [r, theta, phi]

def spherical_to_cartesian(r, theta, phi):

    theta_rad, phi_rad = np.deg2rad(theta), np.deg2rad(phi)
    x = r * np.sin(theta_rad) * np.cos(phi_rad)
    y = r * np.sin(theta_rad) * np.sin(phi_rad)
    z = r * np.cos(theta_rad)

    return [x,y,z]


def rotate_vector(moment_vector, theta_deg, phi_deg):
    """
    Applies a rotation to a moment vector using Euler angles.
    Rotation is R = R_z(phi) @ R_y(theta).
    """
    theta = np.deg2rad(theta_deg)
    phi = np.deg2rad(phi_deg)

    # Rotation matrix around y-axis
    R_y = np.array([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)]
    ])

    # Rotation matrix around z-axis
    R_z = np.array([
        [np.cos(phi), -np.sin(phi), 0],
        [np.sin(phi), np.cos(phi), 0],
        [0, 0, 1]
    ])

    # Combined rotation matrix
    R = R_z @ R_y

    # Apply rotation to the moment vector
    new_moment = R @ np.array(moment_vector)

    return new_moment.tolist()

