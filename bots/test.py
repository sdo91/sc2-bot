from math import sqrt


buffer_y = 3

unit_x = 50
unit_y = 50

point_x = 10
point_y = 5

hypotenuse = 10


opposite = buffer_y - point_y



opposite_length = 26 - point_y


adjacent = sqrt(hypotenuse ** 2 - opposite_length ** 2)

print(adjacent, buffer_y)

print(sqrt(adjacent**2 + buffer_y**2))