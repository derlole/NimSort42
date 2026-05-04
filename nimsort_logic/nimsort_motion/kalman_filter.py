class KalmanFilterPosVel:
    def __init__(self, q_pos=1e-4, q_vel=1e-2, r=1e-1):
        # Zustand: [position, velocity]
        self.x = [0.0, 0.0]

        # Kovarianzmatrix
        self.P = [[1.0, 0.0],
                  [0.0, 1.0]]

        self.q_pos = q_pos
        self.q_vel = q_vel
        self.r = r

    def update(self, measurement, dt):
        # ─── Prediction ─────────────────────────────

        # Zustandsvorhersage
        x_pred = [
            self.x[0] + self.x[1] * dt,
            self.x[1]
        ]

        # Systemmatrix F
        F = [
            [1.0, dt],
            [0.0, 1.0]
        ]

        # Prozessrauschen Q
        Q = [
            [self.q_pos, 0.0],
            [0.0, self.q_vel]
        ]

        # P = F P F^T + Q
        P = self.P
        P_pred = [
            [
                F[0][0]*P[0][0] + F[0][1]*P[1][0],
                F[0][0]*P[0][1] + F[0][1]*P[1][1]
            ],
            [
                F[1][0]*P[0][0] + F[1][1]*P[1][0],
                F[1][0]*P[0][1] + F[1][1]*P[1][1]
            ]
        ]

        # FPF^T
        P_pred = [
            [
                P_pred[0][0]*F[0][0] + P_pred[0][1]*F[0][1],
                P_pred[0][0]*F[1][0] + P_pred[0][1]*F[1][1]
            ],
            [
                P_pred[1][0]*F[0][0] + P_pred[1][1]*F[0][1],
                P_pred[1][0]*F[1][0] + P_pred[1][1]*F[1][1]
            ]
        ]

        # + Q
        P_pred[0][0] += Q[0][0]
        P_pred[1][1] += Q[1][1]

        # ─── Update ─────────────────────────────

        # Messmatrix H = [1, 0]
        y = measurement - x_pred[0]

        S = P_pred[0][0] + self.r

        K = [
            P_pred[0][0] / S,
            P_pred[1][0] / S
        ]

        # Zustand update
        self.x[0] = x_pred[0] + K[0] * y
        self.x[1] = x_pred[1] + K[1] * y

        # Kovarianz update
        self.P = [
            [
                (1 - K[0]) * P_pred[0][0],
                (1 - K[0]) * P_pred[0][1]
            ],
            [
                -K[1] * P_pred[0][0] + P_pred[1][0],
                -K[1] * P_pred[0][1] + P_pred[1][1]
            ]
        ]

        return self.x  # [position, velocity]

    def reset(self, pos=0.0, vel=0.0):
        self.x = [pos, vel]
        self.P = [[1.0, 0.0], [0.0, 1.0]]