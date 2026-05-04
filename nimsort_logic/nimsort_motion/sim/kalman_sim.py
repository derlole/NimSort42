from nimsort_motion.kalman_filter import KalmanFilterPosVel
import random
import matplotlib.pyplot as plt

dt = 0.1
steps = 200

max_vel = 0.07
max_acc = 0.02

# "echter" Zustand
true_pos = 0.0
true_vel = 0.0

kf = KalmanFilterPosVel()

# Logging
true_positions = []
measured_positions = []
estimated_positions = []
estimated_velocities = []

# ─────────────────────────────
# Simulation Loop
# ─────────────────────────────
for i in range(steps):

    # zufällige Beschleunigung (begrenzt)
    acc = random.uniform(-max_acc, max_acc)

    # Geschwindigkeit integrieren + clamp
    true_vel += acc * dt
    true_vel = max(min(true_vel, max_vel), -max_vel)

    # Position integrieren
    true_pos += true_vel * dt

    # Begrenzung auf [0, 1]
    if true_pos < 0:
        true_pos = 0
        true_vel = 0
    elif true_pos > 1.0:
        true_pos = 1.0
        true_vel = 0

    # Messrauschen
    noise = random.gauss(0, 0.02)
    measurement = true_pos + noise

    # Kalman Update
    est_pos, est_vel = kf.update(measurement, dt)

    # Logging
    true_positions.append(true_pos)
    measured_positions.append(measurement)
    estimated_positions.append(est_pos)
    estimated_velocities.append(est_vel)


# ─────────────────────────────
# Plot
# ─────────────────────────────
plt.figure()
plt.plot(true_positions, label="True Position")
plt.plot(measured_positions, label="Measurement", linestyle="dotted")
plt.plot(estimated_positions, label="Kalman Position")
plt.legend()
plt.title("Position")

plt.figure()
plt.plot(estimated_velocities, label="Estimated Velocity")
plt.legend()
plt.title("Velocity")

plt.show()