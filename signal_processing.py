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
    list: acceleration relative to the Word Frame axes [east, north, up]
    returns [] if conversion cannot be calculated due to missing data
    """
    # Convert inputs to numpy arrays
    lin_acc = np.array(linear_acceleration)
    rot_vec = np.array(rotation_vector)
    
    # Convert the rotation vector to a quaternion
    # Handle the rotation vector format
    if len(rot_vec) == 3: # compute the scalar if absent
        xyz_squared_sum = np.sum(rot_vec**2)
        # Handle for square root of a negative, due to rounding errors
        scalar = np.sqrt(max(0.0, 1.0 - xyz_squared_sum))
        quaternion = np.array([rot_vec[0], rot_vec[1], rot_vec[2], scalar])
    elif len(rot_vec) >= 4:
        quaternion = rot_vec[:4]
    else:
        print(len(rot_vec))
        return [] # return empty list if conversion cannot be calculated
        
    # Create rotation object from the quaternion
    device_rotation = Rotation.from_quat(quaternion)
    
    # Apply rotation to the acceleration vector
    earth_acc = device_rotation.apply(lin_acc)
    
    return [float(i) for i in earth_acc]


def calculate_user_acceleration(rotation_vector: list[float], linear_acceleration: list[float]) -> list[float]:
    """
    Transforms linear acceleration from the Device Frame (x, y, z) to the User Frame (right, forward, up) 
    by stripping out compass heading (yaw).
    
    Parameters:
    rotation_vector (list): [x, y, z, w] or [x, y, z] where w = scalar
    linear_acceleration (list): [x, y, z]
    
    Returns:
    list: acceleration relative to the user [right, forward, up]
    returns [] if conversion cannot be calculated due to missing data
    """
    
    # Convert inputs to numpy arrays
    lin_acc = np.array(linear_acceleration)
    rot_vec = np.array(rotation_vector)
    
    # Convert the rotation vector to a quaternion
    # Handle the rotation vector format
    if len(rot_vec) == 3: # compute the scalar if absent
        xyz_squared_sum = np.sum(rot_vec**2)
        scalar = np.sqrt(max(0.0, 1.0 - xyz_squared_sum))
        quaternion = np.array([rot_vec[0], rot_vec[1], rot_vec[2], scalar])
    elif len(rot_vec) >= 4:
        quaternion = rot_vec[:4]
    else:
        return [] # return empty list if conversion cannot be calculated

    # Create rotation object from the quaternion
    device_rotation = Rotation.from_quat(quaternion)

    # Extract Euler angles in zyx order
    # z = Yaw (heading), y = Pitch, x = Roll
    yaw, pitch, roll = device_rotation.as_euler('zyx', degrees=False)
    
    # Create new rotation object ignoring Yaw (z-rotation = 0), containing only tilt data
    tilt_rotation = Rotation.from_euler('zyx', [0, pitch, roll], degrees=False)
    
    # Apply tilt-only transformation to the raw device acceleration
    user_acc = tilt_rotation.apply(lin_acc)
    
    # Map output array directly to [Right, Forward, Up]
    # By setting yaw = 0, the original phone forward direction becomes the User Frame forward
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
        Tracks movement state based on magnitude for Zero Update Position and Timing
        
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