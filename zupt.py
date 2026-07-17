import numpy as np

class LinearZuptTracker:
    def __init__(self, window_size: int = 10, variance_threshold: float = 0.01):
        """
        Initializes the ZUPT tracker.
        
        Parameters:
        window_size (int): number of sample used for variance checking
        variance_threshold (float): maximum variance in acceleration magnitude to consider 'stationary'
        """
        self.window_size = window_size
        self.threshold = variance_threshold
        
        # State vectors [x, y, z]
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        
        # History buffers
        self.accel_history = []
        self.last_timestamp = None

    def update(self, timestamp: float, linear_accel: list):
        """
        Updates the tracking state with a new sensor reading.

        Parameters: 
        timestamp (float): current sensor event timestamp in seconds
        linear_accel (list): linear acceleration vector [x, y, z]

        Returns:
        tuple: (current_position, current_velocity, is_stationary)
        """
        
        # Conver acceleration to np array
        accel = np.array(linear_accel)
        
        # Handle first frame initialization
        if self.last_timestamp is None:
            self.last_timestamp = timestamp
            self.accel_history.append(accel)
            return self.position, self.velocity, True
            
        dt = timestamp - self.last_timestamp
        self.last_timestamp = timestamp
        
        # 1. Update acceleration history buffer
        self.accel_history.append(accel)
        if len(self.accel_history) > self.window_size:
            self.accel_history.pop(0)
            
        # 2. Determine if stationary (ZUPT Check)
        is_stationary = False
        if len(self.accel_history) == self.window_size:
            # Calculate magnitudes of all acceleration vectors in the window
            magnitudes = [np.linalg.norm(a) for a in self.accel_history]
            # Check the variance of the magnitudes
            variance = np.var(magnitudes)
            
            if variance < self.threshold:
                is_stationary = True

        # 3. Apply Dead Reckoning or ZUPT
        if is_stationary:
            # Slam velocity back to zero to kill drift
            self.velocity = np.array([0.0, 0.0, 0.0])
        else:
            # Integrate acceleration to velocity: v = v0 + a * dt
            self.velocity += accel * dt
            
        # Integrate velocity to position: p = p0 + v * dt
        self.position += self.velocity * dt
        
        return self.position.copy(), self.velocity.copy(), is_stationary

# ==========================================
# Example Usage Simulation
# ==========================================
if __name__ == "__main__":
    import random
    
    # Instantiate tracker (Tweak thresholds based on your phone's actual sensor noise)
    tracker = LinearZuptTracker(window_size=5, variance_threshold=0.005)
    
    # Simulate data stream: 100Hz sampling rate (dt = 0.01s)
    dt = 0.01
    current_time = 0.0
    
    print(f"{'Time (s)':<10} | {'Status':<10} | {'Velocity (X,Y,Z)':<30} | {'Position (X,Y,Z)':<30}")
    print("-" * 90)
    
    for step in range(60):
        current_time += dt
        
        # Simulate 3 phases: Stationary -> Sudden lurch forward in X -> Stationary again
        if step < 20:
            # Phase 1: Stationary with minor electronic sensor noise
            simulated_accel = [random.uniform(-0.01, 0.01), 0.0, 0.0]
        elif step < 40:
            # Phase 2: Accelerated movement forward along X axis (e.g., 2.5 m/s^2)
            simulated_accel = [2.5 + random.uniform(-0.02, 0.02), 0.0, 0.0]
        else:
            # Phase 3: Abrupt stop, stationary again with sensor noise
            # (Without ZUPT, the velocity accumulated from noise here would cause position to run away)
            simulated_accel = [random.uniform(-0.01, 0.01), 0.0, 0.0]
            
        pos, vel, stationary = tracker.update(current_time, simulated_accel)
        
        status_str = "STATIONARY" if stationary else "MOVING"
        pos_str = f"[{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]"
        vel_str = f"[{vel[0]:.3f}, {vel[1]:.3f}, {vel[2]:.3f}]"
        
        # Print every 5th sample to keep output clean
        if step % 5 == 0:
            print(f"{current_time:<10.2f} | {status_str:<10} | {vel_str:<30} | {pos_str:<30}")