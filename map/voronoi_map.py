#import numpy as np
#from PIL import Image, ImageDraw
#from scipy.spatial import Voronoi
#import random
#import fpsample
#
#image_path = 'insert.png'
#image = Image.open(image_path).convert('L')
#image_array = np.array(image)
#spixels = np.argwhere(image_array == 255)
#
#num_points = min(80, len(spixels))
#
#chosen_points_idx = fpsample.bucket_fps_kdline_sampling(spixels, num_points, h=3)
#chosen_points = spixels[chosen_points_idx]
#
#used_colors = set()
#colors = []
#for _ in range(num_points):
#    while True:
#        #random_color = tuple(random.randint(0, 29) for _ in range(3))
#        #random_color = tuple(random.randint(30, 99) for _ in range(3))
#        random_color = tuple(random.randint(100, 255) for _ in range(3))
#        if random_color not in used_colors:
#            used_colors.add(random_color)
#            colors.append(random_color)
#            break
#
#points = chosen_points[:, [1, 0]]  # Voronoi expects (x, y) format
#vor = Voronoi(points)
#
#output_image = Image.new("RGB", image.size, "white")
#draw = ImageDraw.Draw(output_image)
#
#for i, region_idx in enumerate(vor.point_region):
#    region = vor.regions[region_idx]
#    if not -1 in region:
#        polygon = [vor.vertices[i] for i in region]
#        if polygon:
#            polygon = np.array(polygon)
#            polygon = [tuple(p) for p in polygon]
#            color = colors[i]
#            draw.polygon(polygon, fill=color)
#
#output_image.save('voronoi_shapes.png')
#
#print("The Voronoi shapes image has been saved as 'voronoi_shapes.png'.")
import matplotlib.pyplot as pl
import numpy as np
import scipy as sp
import scipy.spatial
import sys
from PIL import Image, ImageDraw
import fpsample
import random

eps = sys.float_info.epsilon

image_path = 'insert.png'
image = Image.open(image_path).convert('L')
image_array = np.array(image)
spixels = np.argwhere(image_array == 255)

n_towers = min(80, len(spixels))
chosen_points_idx = fpsample.bucket_fps_kdline_sampling(spixels, n_towers, h=3)
chosen_points = spixels[chosen_points_idx]

towers = chosen_points
bounding_box = np.array([0, image.width, 0, image.height]) # [x_min, x_max, y_min, y_max]

used_colors = set()
colors = []
for _ in range(n_towers):
    while True:
        #random_color = tuple(random.randint(0, 29) for _ in range(3))
        #random_color = tuple(random.randint(30, 99) for _ in range(3))
        random_color = tuple(random.randint(100, 255) for _ in range(3))
        if random_color not in used_colors:
            used_colors.add(random_color)
            colors.append(random_color)
            break

def in_box(towers, bounding_box):
    return np.logical_and(np.logical_and(bounding_box[0] <= towers[:, 0],
                                         towers[:, 0] <= bounding_box[1]),
                          np.logical_and(bounding_box[2] <= towers[:, 1],
                                         towers[:, 1] <= bounding_box[3]))

def voronoi(towers, bounding_box):
    # Select towers inside the bounding box
    i = in_box(towers, bounding_box)
    # Mirror points
    points_center = towers[i, :]
    points_left = np.copy(points_center)
    points_left[:, 0] = bounding_box[0] - (points_left[:, 0] - bounding_box[0])
    points_right = np.copy(points_center)
    points_right[:, 0] = bounding_box[1] + (bounding_box[1] - points_right[:, 0])
    points_down = np.copy(points_center)
    points_down[:, 1] = bounding_box[2] - (points_down[:, 1] - bounding_box[2])
    points_up = np.copy(points_center)
    points_up[:, 1] = bounding_box[3] + (bounding_box[3] - points_up[:, 1])
    points = np.append(points_center,
                       np.append(np.append(points_left,
                                           points_right,
                                           axis=0),
                                 np.append(points_down,
                                           points_up,
                                           axis=0),
                                 axis=0),
                       axis=0)
    # Compute Voronoi
    vor = sp.spatial.Voronoi(points)
    # Filter regions
    regions = []
    for region in vor.regions:
        flag = True
        for index in region:
            if index == -1:
                flag = False
                break
            else:
                x = vor.vertices[index, 0]
                y = vor.vertices[index, 1]
                if not(bounding_box[0] - eps <= x and x <= bounding_box[1] + eps and
                       bounding_box[2] - eps <= y and y <= bounding_box[3] + eps):
                    flag = False
                    break
        if region != [] and flag:
            regions.append(region)
    vor.filtered_points = points_center
    vor.filtered_regions = regions
    return vor

def centroid_region(vertices):
    # Polygon's signed area
    A = 0
    # Centroid's x
    C_x = 0
    # Centroid's y
    C_y = 0
    for i in range(0, len(vertices) - 1):
        s = (vertices[i, 0] * vertices[i + 1, 1] - vertices[i + 1, 0] * vertices[i, 1])
        A = A + s
        C_x = C_x + (vertices[i, 0] + vertices[i + 1, 0]) * s
        C_y = C_y + (vertices[i, 1] + vertices[i + 1, 1]) * s
    A = 0.5 * A
    C_x = (1.0 / (6.0 * A)) * C_x
    C_y = (1.0 / (6.0 * A)) * C_y
    return np.array([[C_x, C_y]])

vor = voronoi(towers, bounding_box)

fig = pl.figure()
ax = fig.gca()
# Plot initial points
ax.plot(vor.filtered_points[:, 0], vor.filtered_points[:, 1], 'b.')
# Plot ridges points
for region in vor.filtered_regions:
    vertices = vor.vertices[region, :]
    ax.plot(vertices[:, 0], vertices[:, 1], 'go')
# Plot ridges
for region in vor.filtered_regions:
    vertices = vor.vertices[region + [region[0]], :]
    ax.plot(vertices[:, 0], vertices[:, 1], 'k-')
# Compute and plot centroids
centroids = []
for region in vor.filtered_regions:
    vertices = vor.vertices[region + [region[0]], :]
    centroid = centroid_region(vertices)
    centroids.append(list(centroid[0, :]))
    ax.plot(centroid[:, 0], centroid[:, 1], 'r.')

ax.set_xlim([-0.1, image.width + 0.1])
ax.set_ylim([-0.1, image.height + 0.1])
pl.savefig("bounded_voronoi.png", dpi=640)

# Kurashi
#output_image = Image.new("RGB", image.size, "white")
#draw = ImageDraw.Draw(output_image)
#
#i = 0
#for region in vor.filtered_regions:
#    polygon = [vor.vertices[i] for i in region]
#    if polygon:
#        polygon = np.array(polygon)
#        polygon = [tuple(p) for p in polygon]
#        color = colors[i]
#        draw.polygon(polygon, fill=color)
#        i += 1
#
#output_image.save('voronoi_shapes.png')

# Create a figure with the specified size
width = image.width
height = image.height
fig, ax = pl.subplots(figsize=(width / 100, height / 100), dpi=100)

# Loop through each Voronoi region and plot them with a random color
for region_index in vor.filtered_regions:
    if not -1 in region_index and len(region_index) > 0:
        polygon = [vor.vertices[i] for i in region_index]
        color = np.random.rand(3,)  # Random color for each region
        pl.fill(*zip(*polygon), color=color, antialiased=False)

# Set axis limits and hide axis
ax.set_xlim(0, width)
ax.set_ylim(0, height)
ax.axis('off')

# Save the image
pl.savefig('voronoi_from_heightmap.png', bbox_inches='tight', pad_inches=0)
pl.close()