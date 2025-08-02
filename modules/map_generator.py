import random
import json
from typing import List, Dict, Tuple, Optional
import math

class MapGenerator:
    """
    Advanced Map Generator for Tower Defense Game
    Supports procedural generation with themes, difficulty scaling, and validation
    """
    
    def __init__(self):
        self.themes = {
            'forest': {
                'name': 'Forest',
                'obstacles': ['tree', 'bush', 'water', 'rock'],
                'colors': {'path': '#8B7355', 'bg': '#6b8e6b'},
                'sprites': {
                    'tree': 'tree_1', 'bush': 'bush_1', 
                    'water': 'water_1', 'rock': 'rock_1'
                }
            },
            'desert': {
                'name': 'Desert',
                'obstacles': ['cactus', 'rock', 'oasis', 'dune'],
                'colors': {'path': '#D2B48C', 'bg': '#F4A460'},
                'sprites': {
                    'cactus': 'cactus_1', 'rock': 'desert_rock_1',
                    'oasis': 'oasis_1', 'dune': 'dune_1'
                }
            },
            'snow': {
                'name': 'Snow',
                'obstacles': ['ice', 'snowman', 'frozen_tree', 'ice_rock'],
                'colors': {'path': '#B0C4DE', 'bg': '#F0F8FF'},
                'sprites': {
                    'ice': 'ice_1', 'snowman': 'snowman_1',
                    'frozen_tree': 'frozen_tree_1', 'ice_rock': 'ice_rock_1'
                }
            },
            'lava': {
                'name': 'Lava',
                'obstacles': ['volcano_rock', 'lava_pool', 'obsidian', 'fire_crystal'],
                'colors': {'path': '#8B0000', 'bg': '#FF4500'},
                'sprites': {
                    'volcano_rock': 'volcano_rock_1', 'lava_pool': 'lava_pool_1',
                    'obsidian': 'obsidian_1', 'fire_crystal': 'fire_crystal_1'
                }
            }
        }
        
        self.difficulty_settings = {
            'easy': {'path_length': 8, 'turns': 2, 'obstacles': 3},
            'medium': {'path_length': 12, 'turns': 4, 'obstacles': 6},
            'hard': {'path_length': 16, 'turns': 6, 'obstacles': 10},
            'nightmare': {'path_length': 20, 'turns': 8, 'obstacles': 15}
        }
        
        self.complexity_patterns = {
            'linear': self._generate_linear_path,
            'curved': self._generate_curved_path,
            'maze': self._generate_maze_path,
            'spiral': self._generate_spiral_path
        }
    
    def generate_map(self, difficulty: str = 'medium', theme: str = 'forest', 
                    size: str = 'medium', complexity: str = 'curved', 
                    custom_name: str = None) -> Dict:
        """
        Generate a complete map with specified parameters
        """
        # Map dimensions based on size
        size_settings = {
            'small': (25, 20),
            'medium': (32, 24), 
            'large': (40, 30)
        }
        
        width, height = size_settings.get(size, (32, 24))
        settings = self.difficulty_settings[difficulty]
        theme_data = self.themes[theme]
        
        # Generate unique map ID
        map_id = self._generate_map_id()
        
        # Generate path using selected complexity
        path_generator = self.complexity_patterns[complexity]
        start, path = path_generator(width, height, settings)
        
        # Generate obstacles
        obstacles = self._generate_obstacles(width, height, start, path, 
                                           settings['obstacles'], theme_data)
        
        # Create map data structure
        map_data = {
            'id': map_id,
            'name': custom_name or f"{theme_data['name']} {complexity.title()} ({difficulty.title()})",
            'start': start,
            'path': path,
            'obstacles': obstacles,
            'difficulty': difficulty,
            'theme': theme,
            'size': size,
            'complexity': complexity,
            'dimensions': {'width': width, 'height': height},
            'generated': True,
            'colors': theme_data['colors']
        }
        
        # Validate the map
        if self._validate_map(map_data):
            return map_data
        else:
            # If validation fails, try again with simpler settings
            return self.generate_map(difficulty, theme, size, 'linear', custom_name)
    
    def _generate_linear_path(self, width: int, height: int, settings: Dict) -> Tuple[Dict, List[Dict]]:
        """Generate a simple linear path with some variation"""
        start_y = height // 2
        start = {'x': 0, 'y': start_y}
        
        path = []
        current_x = 2
        current_y = start_y
        
        target_length = min(settings['path_length'], width - 3)
        
        for i in range(target_length):
            # Add some vertical variation
            if i > 0 and i < target_length - 1 and random.random() < 0.3:
                variation = random.choice([-1, 1])
                new_y = max(1, min(height - 2, current_y + variation))
                if new_y != current_y:
                    path.append({'x': current_x, 'y': new_y})
                    current_y = new_y
                    current_x += 1
            
            path.append({'x': current_x, 'y': current_y})
            current_x += 2
            
            if current_x >= width - 1:
                break
        
        return start, path
    
    def _generate_curved_path(self, width: int, height: int, settings: Dict) -> Tuple[Dict, List[Dict]]:
        """Generate a curved path with smooth turns"""
        start_side = random.choice(['left', 'top', 'bottom'])
        
        if start_side == 'left':
            start = {'x': 0, 'y': random.randint(3, height - 4)}
        elif start_side == 'top':
            start = {'x': random.randint(3, width - 4), 'y': 0}
        else:  # bottom
            start = {'x': random.randint(3, width - 4), 'y': height - 1}
        
        path = []
        current_x, current_y = start['x'], start['y']
        
        # Target end point
        if start_side == 'left':
            target_x, target_y = width - 1, random.randint(3, height - 4)
        elif start_side == 'top':
            target_x, target_y = random.randint(3, width - 4), height - 1
        else:
            target_x, target_y = random.randint(3, width - 4), 0
        
        # Generate curved path using waypoints
        waypoints = self._generate_waypoints(current_x, current_y, target_x, target_y, 
                                            settings['turns'], width, height)
        
        for waypoint in waypoints:
            # Create smooth path to waypoint
            path.extend(self._create_smooth_path(current_x, current_y, 
                                               waypoint['x'], waypoint['y']))
            current_x, current_y = waypoint['x'], waypoint['y']
        
        return start, path
    
    def _generate_maze_path(self, width: int, height: int, settings: Dict) -> Tuple[Dict, List[Dict]]:
        """Generate a maze-like path with multiple turns"""
        start = {'x': 0, 'y': height // 2}
        path = []
        
        current_x, current_y = 2, start['y']
        direction = 'right'
        
        while current_x < width - 3:
            # Move in current direction
            steps = random.randint(2, 4)
            
            for _ in range(steps):
                if direction == 'right':
                    current_x += 1
                elif direction == 'up':
                    current_y -= 1
                elif direction == 'down':
                    current_y += 1
                
                # Bounds checking
                current_x = max(1, min(width - 2, current_x))
                current_y = max(1, min(height - 2, current_y))
                
                path.append({'x': current_x, 'y': current_y})
                
                if current_x >= width - 3:
                    break
            
            # Change direction randomly
            if current_x < width - 3:
                if direction == 'right':
                    direction = random.choice(['up', 'down'])
                else:
                    direction = 'right'
        
        return start, path
    
    def _generate_spiral_path(self, width: int, height: int, settings: Dict) -> Tuple[Dict, List[Dict]]:
        """Generate a spiral-like path"""
        center_x, center_y = width // 2, height // 2
        start = {'x': 0, 'y': center_y}
        
        path = []
        current_x, current_y = 2, center_y
        
        # Create spiral towards center, then out
        radius = 1
        angle = 0
        
        while current_x < width - 3 and len(path) < settings['path_length']:
            # Calculate spiral position
            spiral_x = int(center_x + radius * math.cos(angle))
            spiral_y = int(center_y + radius * math.sin(angle))
            
            # Bounds checking
            spiral_x = max(1, min(width - 2, spiral_x))
            spiral_y = max(1, min(height - 2, spiral_y))
            
            # Create path to spiral position
            if abs(spiral_x - current_x) <= 2 and abs(spiral_y - current_y) <= 2:
                path.append({'x': spiral_x, 'y': spiral_y})
                current_x, current_y = spiral_x, spiral_y
            
            angle += 0.5
            radius += 0.1
            
            # Move towards exit
            if radius > min(width, height) // 3:
                current_x += 1
                path.append({'x': current_x, 'y': current_y})
        
        return start, path
    
    def _generate_waypoints(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                           num_turns: int, width: int, height: int) -> List[Dict]:
        """Generate waypoints for curved paths"""
        waypoints = []
        
        for i in range(num_turns):
            progress = (i + 1) / (num_turns + 1)
            
            # Interpolate position with some randomness
            base_x = int(start_x + (end_x - start_x) * progress)
            base_y = int(start_y + (end_y - start_y) * progress)
            
            # Add random offset
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            
            waypoint_x = max(2, min(width - 3, base_x + offset_x))
            waypoint_y = max(2, min(height - 3, base_y + offset_y))
            
            waypoints.append({'x': waypoint_x, 'y': waypoint_y})
        
        # Add final waypoint
        waypoints.append({'x': end_x, 'y': end_y})
        
        return waypoints
    
    def _create_smooth_path(self, start_x: int, start_y: int, 
                           end_x: int, end_y: int) -> List[Dict]:
        """Create a smooth path between two points"""
        path = []
        
        dx = end_x - start_x
        dy = end_y - start_y
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            return []
        
        for i in range(1, steps + 1):
            progress = i / steps
            x = int(start_x + dx * progress)
            y = int(start_y + dy * progress)
            path.append({'x': x, 'y': y})
        
        return path
    
    def _generate_obstacles(self, width: int, height: int, start: Dict, 
                           path: List[Dict], num_obstacles: int, theme_data: Dict) -> List[Dict]:
        """Generate obstacles that don't block the path"""
        obstacles = []
        path_positions = {(start['x'], start['y'])}
        
        # Add all path positions to blocked set
        for point in path:
            path_positions.add((point['x'], point['y']))
            # Also block adjacent positions to path
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    path_positions.add((point['x'] + dx, point['y'] + dy))
        
        obstacle_types = theme_data['obstacles']
        sprites = theme_data['sprites']
        
        attempts = 0
        while len(obstacles) < num_obstacles and attempts < num_obstacles * 3:
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)
            
            if (x, y) not in path_positions:
                obstacle_type = random.choice(obstacle_types)
                obstacles.append({
                    'x': x,
                    'y': y,
                    'attributes': {
                        'type': obstacle_type,
                        'sprite_id': sprites[obstacle_type]
                    }
                })
                # Block this position for future obstacles
                path_positions.add((x, y))
            
            attempts += 1
        
        return obstacles
    
    def _validate_map(self, map_data: Dict) -> bool:
        """Validate that the generated map is playable"""
        # Check that path exists and is reasonable length
        if len(map_data['path']) < 3:
            return False
        
        # Check that start and end are different
        start = map_data['start']
        end = map_data['path'][-1]
        if abs(start['x'] - end['x']) < 5:
            return False
        
        # Check that obstacles don't block path
        path_positions = {(start['x'], start['y'])}
        for point in map_data['path']:
            path_positions.add((point['x'], point['y']))
        
        for obstacle in map_data['obstacles']:
            if (obstacle['x'], obstacle['y']) in path_positions:
                return False
        
        return True
    
    def _generate_map_id(self) -> int:
        """Generate a unique map ID"""
        return random.randint(1000, 9999)
    
    def get_themes(self) -> Dict:
        """Return available themes"""
        return {k: {'name': v['name'], 'colors': v['colors']} 
                for k, v in self.themes.items()}
    
    def get_difficulties(self) -> List[str]:
        """Return available difficulty levels"""
        return list(self.difficulty_settings.keys())
    
    def get_complexities(self) -> List[str]:
        """Return available complexity patterns"""
        return list(self.complexity_patterns.keys())
