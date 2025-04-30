import math


def fov(tilemap, center, radius):
    
    visible = set()
    num_rays = 1 << min(12, radius + 1)
    
    for i in range(num_rays):
        
        angle = 2 * math.pi * i / num_rays
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        distance = 0
        step = 1 / max(abs(cos_a), abs(sin_a))
        
        while distance <= radius:
            
            x = center[0] + distance * cos_a
            y = center[1] + distance * sin_a
            cell = round(x), round(y)
            visible.add(cell)
            tile = tilemap.get_tile(cell)
            
            if not tile.is_transparent:
                break
                
            distance += step
            
    return visible
