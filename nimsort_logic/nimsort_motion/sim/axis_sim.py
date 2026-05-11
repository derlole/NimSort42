"""
axis_sim.py
---
Simulation für die Axis-Klasse, die den Trajectory Planner und Controller beinhaltet.
"""

import matplotlib.pyplot as plt
import numpy as np
from nimsort_motion.axis import Axis
from nimsort_motion.controller import Controller
from nimsort_motion.trajectroy_planner import TrajectoryPlanner

def run_axis_simulation():
    """
    Simuliert die Bewegung einer Achse von 0.0 zu 1.0 m.
    """
    # Parameter
    dt = 0.01  # Zeitsschritt [s]
    total_time = 10.0  # Gesamtzeit [s]
    steps = int(total_time / dt)

    # Komponenten initialisieren
    planner = TrajectoryPlanner(max_velocity=0.05, max_acceleration=0.02)
    controller = Controller(kp=1.0, kd=2.0, output_limit=0.02, kff=0.875)
    axis = Axis(name="X", controller=controller, trajectory_planner=planner, initial_position=0.0)

    # Ziel setzen
    target_position = 0.01
    axis.set_target(target_position)

    # Logging
    times = []
    positions = []
    velocities = []
    accelerations = []
    target_positions = []

    # Simulierte Position (für Update)
    current_position = 0.0
    current_velocity = 0.0

    for i in range(steps):
        t = i * dt
        times.append(t)

        # Axis Update (berechnet Beschleunigung)
        accel = axis.update(current_position, dt)
        accelerations.append(accel)

        # Physik simulieren: Position und Geschwindigkeit aktualisieren
        current_velocity += accel * dt
        current_position += current_velocity * dt

        # Begrenzungen (z.B. 0 bis 1.5 m)
        if current_position < 0.0:
            current_position = 0.0
            current_velocity = 0.0
        elif current_position > 1.5:
            current_position = 1.5
            current_velocity = 0.0

        positions.append(current_position)
        velocities.append(current_velocity)
        target_positions.append(target_position)

        # Abbruchbedingung, wenn Ziel erreicht
        if axis.target_reached:
            print(f"Ziel erreicht bei t={t:.2f}s, pos={current_position:.4f}m")
            break

    # Plots
    plt.figure(figsize=(12, 8))

    plt.subplot(3, 1, 1)
    plt.plot(times, positions, label='Position [m]')
    plt.plot(times, target_positions, label='Target [m]', linestyle='--')
    plt.ylabel('Position [m]')
    plt.legend()
    plt.title('Axis Simulation')

    plt.subplot(3, 1, 2)
    plt.plot(times, velocities, label='Velocity [m/s]')
    plt.ylabel('Velocity [m/s]')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(times, accelerations, label='Acceleration [m/s²]')
    plt.xlabel('Time [s]')
    plt.ylabel('Acceleration [m/s²]')
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_axis_simulation()