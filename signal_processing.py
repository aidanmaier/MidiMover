import numpy as np
from math import hypot
from scipy.spatial.transform import Rotation

def calculate_world_acceleration(rotation_vector: list[float], linear_acceleration: list[float]) -> list[float]:
    """
    Transforms linear acceleration from the Device Frame (x, y, z) to the World Frame (east, north, up).
    
    Parameters:
    rotation_vector (list): [x, y, z] or [x, y, z, w] where w = scalar
    linear_acceleration (list): [x, y, z]
    
    Returns:
    list: acceleration relative to the World Frame axes [east, north, up]
    returns [] if conversion cannot be calculated due to missing data
    """
    
    lin_acc = np.array(linear_acceleration)
    rot_vec = np.array(rotation_vector)

    # Handle vector formatting
    if len(lin_acc) != 3 or len(rot_vec) < 3:
        return [] # return empty list if conversion cannot be calculated
    
    if len(rot_vec) == 3: # compute the scalar if absent
        xyz_squared_sum = np.sum(rot_vec**2)
        # Handle for square root of a negative, due to rounding errors
        w = np.sqrt(max(0.0, 1.0 - xyz_squared_sum))
        x, y, z = rot_vec
        quaternion = np.array([x, y, z, w])
    else:
        quaternion = rot_vec[:4]
        
    # Create rotation object from the quaternion
    device_rotation = Rotation.from_quat(quaternion)
    
    # Apply rotation to the acceleration vector
    world_acc = device_rotation.apply(lin_acc)
    
    return [float(i) for i in world_acc]


def calculate_user_acceleration(rotation_vector: list[float], linear_acceleration: list[float]) -> list[float]:
    """
    Transforms linear acceleration from the Device Frame (x, y, z) to the User Frame (right, forward, up) 
    by stripping out compass heading (yaw) using inverse rotation.

    Parameters:
    rotation_vector (list): [x, y, z] or [x, y, z, w] where w = scalar
    linear_acceleration (list): [x, y, z]
    
    Returns:
    list: acceleration relative to the World Frame axes [right, forward, up]
    returns [] if conversion cannot be calculated due to missing data
    """
    
    lin_acc = np.array(linear_acceleration)
    rot_vec = np.array(rotation_vector)

    # Handle vector formatting
    if len(lin_acc) != 3 or len(rot_vec) < 3:
        return [] # return empty list if conversion cannot be calculated
    
    if len(rot_vec) == 3: # compute the scalar if absent
        xyz_squared_sum = np.sum(rot_vec**2)
        # Handle for square root of a negative, due to rounding errors
        w = np.sqrt(max(0.0, 1.0 - xyz_squared_sum))
        x, y, z = rot_vec
        quaternion = np.array([x, y, z, w])
    else:
        quaternion = rot_vec[:4]
        
    # Create rotation object from the quaternion
    device_rotation = Rotation.from_quat(quaternion)

    # Transform to world coordinates (east, north, up)
    world_acc = device_rotation.apply(lin_acc)

    # Extract heading angle (Yaw) around the global (vertical) Z-axis 
    yaw, _, _ = device_rotation.as_euler('zyx', degrees=False)
    
    # Un-rotate the world frame around the Z-axis by the yaw angle 
    # to align the frame Y-axis with the device forward direction
    yaw_rotation = Rotation.from_euler('z', yaw, degrees=False)
    user_acc = yaw_rotation.inv().apply(world_acc)
    
    return [float(i) for i in user_acc]


def calculate_magnitude(vector: list[float]) -> float:
    """
    Calculates the magnitude of a 3-digit vector.

    Parameters:
    vector (list): [x, y, z]

    Returns:
    float: vector magnitude
    """
    
    # Calculate hypotenuse from vector
    x, y, z = vector

    return hypot(x, y, z)


class MagnitudeZuptTracker:
    def __init__(self, window_size: int = 10, variance_threshold: float = 0.01):
        """
        Tracks movement state based on magnitude variance for Zero Update Position and Timing.
        
        Parameters:
        window_size (int): number of sample used for variance checking
        variance_threshold (float): maximum variance in acceleration magnitude to consider 'stationary'
        """
        
        self.window_size = window_size
        self.threshold = variance_threshold
        
        # Scalar tracking states
        self.distance_traveled = 0.0
        self.speed = 0.0
        self.is_stationary = True
        
        # History buffers
        self.mag_history = []
        self.last_timestamp = None

    def update(self, timestamp, magnitude: float) -> tuple[float, float, bool]:
            """
            Updates tracking using acceleration magnitude.

            Parameters:
            timestamp (float): timestamp in seconds
            magnitude (float): magnitude calculated from linear acceleration vector

            Returns:
            tuple: (distance_traveled in m, speed in m/s, is_stationary as bool)
            """
            
            # Initial timestamp
            if self.last_timestamp is None:
                self.last_timestamp = timestamp
                self.mag_history.append(magnitude)
                return (self.distance_traveled, self.speed, self.is_stationary)
            
            # Calculate elapsed time since last sample (delta time)
            dt = timestamp - self.last_timestamp 
            self.last_timestamp = timestamp
            
            # Update history buffer
            self.mag_history.append(magnitude)
            # Maintain window size
            if len(self.mag_history) > self.window_size:
                self.mag_history.pop(0)
                
            # ZUPT Check on magnitude variance
            # If window is full and variance < threshold, then stationary
            self.is_stationary = False
            if len(self.mag_history) == self.window_size:
                variance = np.var(self.mag_history)
                if variance < self.threshold:
                    self.is_stationary = True

            # Integrate Scalar Speed and Distance
            if self.is_stationary:
                self.speed = 0.0  # Force halt drift
            else:
                # Scale velocity based on magnitude
                self.speed += magnitude * dt
                
            self.distance_traveled += self.speed * dt
            
            return (self.distance_traveled, self.speed, self.is_stationary)