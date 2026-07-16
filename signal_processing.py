import numpy as np
from scipy.spatial.transform import Rotation

def calculate_world_acceleration(rotation_vector: list[float], linear_acceleration: list[float]) -> list[float]:
    """
    Transforms linear acceleration from the Device Frame to the World Frame
    
    Parameters:
    rotation_vector (list): [x, y, z] or [x, y, z, w] where w = scalar
    linear_acceleration (list): [x, y, z]
    
    Returns:
    list: acceleration relative to the Word Frame axes [x, y, z]
    returns [] if conversion cannot be calculated due to missing data
    """
    # Convert inputs to numpy arrays
    lin_acc = np.array(linear_acceleration)
    rot_vec = np.array(rotation_vector)
    
    # Convert the rotation vector to a quaternion
    # Handle the rotation vector format, compute the scalar if absent
    if len(rot_vec) == 3:
        xyz_squared_sum = np.sum(rot_vec**2)
        # Handle for square root of a negative, due to rounding errors
        scalar = np.sqrt(max(0.0, 1.0 - xyz_squared_sum))
        quaternion = np.array([rot_vec[0], rot_vec[1], rot_vec[2], scalar])
    elif len(rot_vec) >= 4:
        quaternion = rot_vec[:4]
    else:
        print(len(rot_vec))
        return [] # return empty list if conversion cannot be calculated
        
    # Create the rotation object from the quaternion
    rotation = Rotation.from_quat(quaternion)
    
    # Apply the rotation to the acceleration vector
    earth_acc = rotation.apply(lin_acc)
    
    return [float(i) for i in earth_acc]
