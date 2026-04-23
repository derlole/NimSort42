class PlausibilityChecker: #TODO finetune the values
    MIN_X = 0.0
    MAX_X = 100.0
    MIN_Y = 0.0
    MAX_Y = 7.0
    MIN_Z = -1.0
    MAX_Z = 2.0

    @classmethod
    def validate(cls, x: float, y: float, z: float):
        errors = []

        if not (cls.MIN_X <= x <= cls.MAX_X):
            errors.append(f"x außerhalb [{cls.MIN_X}, {cls.MAX_X}]")

        if not (cls.MIN_Y <= y <= cls.MAX_Y):
            errors.append(f"y außerhalb [{cls.MIN_Y}, {cls.MAX_Y}]")

        if not (cls.MIN_Z <= z <= cls.MAX_Z):
            errors.append(f"z außerhalb [{cls.MIN_Z}, {cls.MAX_Z}]")

        return len(errors) == 0, errors