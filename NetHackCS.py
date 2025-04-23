import curses
import sys
import signal
import re
from enum import Enum

class Category(Enum):
    ITEMS = 0
    MONSTERS = 1
    COMMANDS = 2
    DUNGEON = 3
    SYMBOLS = 4

class NethackReferenceTUI:
    """
    A Terminal User Interface for searching and displaying NetHack information,
    including items, monsters, commands, and other useful references.
    """
    
    def __init__(self):
        self.screen = None
        self.running = True
        self.current_category = Category.ITEMS
        self.search_query = ""
        self.is_searching = False
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_display_items = 0
        
        # Database of NetHack information
        self.data = self.init_database()
        self.filtered_data = self.data[self.current_category.value]
        
    def init_database(self):
        """Initialize the database of NetHack information."""
        return [
            # ITEMS
            [
                {"name": "Amulet of Yendor", "symbol": '"', "description": "The main objective of the game. Retrieve this from the Wizard of Yendor."},
                {"name": "Long Sword", "symbol": ')', "description": "Damage: 1d8. A standard weapon for Knights and Valkyries."},
                {"name": "Elven Dagger", "symbol": ')', "description": "Damage: 1d5. A light, quick weapon that does extra damage to orcs."},
                {"name": "Wand of Death", "symbol": '/', "description": "Fires a ray that can instantly kill most monsters. Very rare."},
                {"name": "Magic Lamp", "symbol": '(', "description": "Can be rubbed to summon a djinni for a wish. Also provides light."},
                {"name": "Scroll of Enchant Armor", "symbol": '?', "description": "Increases the enchantment of worn armor by +1."},
                {"name": "Scroll of Enchant Weapon", "symbol": '?', "description": "Increases the enchantment of wielded weapon by +1."},
                {"name": "Ring of Teleport Control", "symbol": '=', "description": "Allows controlled teleportation when teleporting."},
                {"name": "Speed Boots", "symbol": '[', "description": "Increase movement speed, allowing for more actions per turn."},
                {"name": "Potion of Healing", "symbol": '!', "description": "Restores 1d8 HP and may cure sickness."},
                {"name": "Potion of Full Healing", "symbol": '!', "description": "Restores all HP and cures sickness."},
                {"name": "Lizard Corpse", "symbol": '%', "description": "Can be eaten to cure petrification and confusion. Doesn't rot."},
                {"name": "Bag of Holding", "symbol": '(', "description": "Reduces the weight of items stored inside it. Can hold many items."},
                {"name": "Cloak of Magic Resistance", "symbol": '[', "description": "Provides magic resistance, protecting from some insta-death attacks."},
                {"name": "Luckstone", "symbol": '*', "description": "Increases luck when carried. Gray stones can be luckstones."},
            ],
            # MONSTERS
            [
                {"name": "Grid Bug", "symbol": 'x', "level": 0, "description": "A weak monster that can only move in cardinal directions."},
                {"name": "Floating Eye", "symbol": 'e', "level": 2, "description": "Can paralyze you if you attack it in melee. Safe to kill with ranged attacks."},
                {"name": "Lich", "symbol": 'L', "level": 11, "description": "Powerful undead spellcaster. Can cast spells and summon monsters."},
                {"name": "Mind Flayer", "symbol": 'h', "level": 9, "description": "Can attack with mind blast to reduce intelligence and wisdom."},
                {"name": "Dragon", "symbol": 'D', "level": 15, "description": "Powerful monster with breath weapon. Different colors have different abilities."},
                {"name": "Purple Worm", "symbol": 'w', "level": 15, "description": "Can swallow you whole. Very dangerous at higher levels."},
                {"name": "Minotaur", "symbol": 'H', "level": 15, "description": "Always follows you through mazes and corridors. Strong in melee."},
                {"name": "Wizard of Yendor", "symbol": '@', "level": 30, "description": "Primary antagonist who guards the Amulet of Yendor. Can steal items and teleport."},
                {"name": "Shopkeeper", "symbol": '@', "level": 12, "description": "Runs shops. Extremely powerful if angered."},
                {"name": "Watch Captain", "symbol": '@', "level": 10, "description": "Leader of the watch. Will attack if you're marked as a wanted criminal."},
            ],
            # COMMANDS
            [
                {"key": "hjkl or arrow keys", "action": "Move in cardinal directions"},
                {"key": "yubn", "action": "Move diagonally"},
                {"key": ",", "action": "Pick up an item"},
                {"key": ".", "action": "Rest one turn"},
                {"key": "s", "action": "Search surroundings"},
                {"key": "i", "action": "Show inventory"},
                {"key": "e", "action": "Eat something"},
                {"key": "q", "action": "Quaff (drink) a potion"},
                {"key": "r", "action": "Read a scroll or book"},
                {"key": "w", "action": "Wield a weapon"},
                {"key": "W", "action": "Wear armor"},
                {"key": "T", "action": "Take off armor"},
                {"key": "d", "action": "Drop an item"},
                {"key": "D", "action": "Drop multiple items"},
                {"key": "t", "action": "Throw an item"},
                {"key": "a", "action": "Apply (use) a tool"},
                {"key": "z", "action": "Zap a wand"},
                {"key": "Z", "action": "Cast a spell"},
                {"key": "#", "action": "Extended command (followed by command name)"},
                {"key": "#offer", "action": "Sacrifice a corpse on an altar"},
                {"key": "#dip", "action": "Dip an item into something"},
                {"key": "#enhance", "action": "View/enhance weapon skills"},
                {"key": "#pray", "action": "Pray to your god for help"},
                {"key": "^", "action": "Show trap under cursor"},
                {"key": ";", "action": "Show remembered monster type at cursor"},
                {"key": ":", "action": "Look at what's on the ground"},
                {"key": "/", "action": "Show known monster types"},
                {"key": "\\", "action": "Show known object types"},
                {"key": "?", "action": "Help menu"},
                {"key": "S", "action": "Save and exit the game"},
            ],
            # DUNGEON FEATURES
            [
                {"symbol": "<", "name": "Staircase up", "description": "Leads to the previous dungeon level."},
                {"symbol": ">", "name": "Staircase down", "description": "Leads to the next dungeon level."},
                {"symbol": "_", "name": "Altar", "description": "Can be used to sacrifice corpses, identify B/U/C status of items."},
                {"symbol": "#", "name": "Corridor", "description": "A passage between rooms."},
                {"symbol": ".", "name": "Floor", "description": "Empty floor tile."},
                {"symbol": "{", "name": "Fountain", "description": "Can be dipped into or quaffed from with varying effects."},
                {"symbol": "}", "name": "Water", "description": "Can be dangerous if you're not waterproof or can't swim."},
                {"symbol": "\\", "name": "Throne", "description": "Can be sat on for random effects, sometimes good."},
                {"symbol": "^", "name": "Trap", "description": "Various traps with different effects. Can be disarmed."},
                {"symbol": "|", "name": "Wall", "description": "Solid wall, blocks movement."},
                {"symbol": "-", "name": "Wall", "description": "Solid wall, blocks movement."},
                {"symbol": "+", "name": "Door", "description": "Can be opened, closed, locked, or broken."},
                {"symbol": "$", "name": "Gold piece", "description": "Currency used for buying items in shops."},
            ],
            # SYMBOLS
            [
                {"symbol": "@", "meaning": "Player or human monster"},
                {"symbol": "a", "meaning": "Ant or other insect"},
                {"symbol": "b", "meaning": "Blob"},
                {"symbol": "c", "meaning": "Canine (dog, wolf, etc.)"},
                {"symbol": "d", "meaning": "Canid (fox, jackal, etc.)"},
                {"symbol": "e", "meaning": "Eye or sphere"},
                {"symbol": "f", "meaning": "Feline or cat"},
                {"symbol": "g", "meaning": "Gremlin or goblin"},
                {"symbol": "h", "meaning": "Humanoid, dwarf, or mind flayer"},
                {"symbol": "i", "meaning": "Imp or minor demon"},
                {"symbol": "j", "meaning": "Jelly"},
                {"symbol": "k", "meaning": "Kobold"},
                {"symbol": "l", "meaning": "Leprechaun"},
                {"symbol": "m", "meaning": "Mimic"},
                {"symbol": "n", "meaning": "Nymph"},
                {"symbol": "o", "meaning": "Orc"},
                {"symbol": "p", "meaning": "Piercer"},
                {"symbol": "q", "meaning": "Quadruped"},
                {"symbol": "r", "meaning": "Rodent"},
                {"symbol": "s", "meaning": "Spider or centipede"},
                {"symbol": "t", "meaning": "Trapper or lurker above"},
                {"symbol": "u", "meaning": "Unicorn or horse"},
                {"symbol": "v", "meaning": "Vortex"},
                {"symbol": "w", "meaning": "Worm"},
                {"symbol": "x", "meaning": "Xan or other mythical/fantastic insect"},
                {"symbol": "y", "meaning": "Yellow light or other light source"},
                {"symbol": "z", "meaning": "Zruty"},
                {"symbol": "A", "meaning": "Angelic being"},
                {"symbol": "B", "meaning": "Bat or bird"},
                {"symbol": "C", "meaning": "Centaur"},
                {"symbol": "D", "meaning": "Dragon"},
                {"symbol": "E", "meaning": "Elemental"},
                {"symbol": "F", "meaning": "Fungus or mold"},
                {"symbol": "G", "meaning": "Gnome"},
                {"symbol": "H", "meaning": "Giant humanoid"},
                {"symbol": "J", "meaning": "Jabberwock"},
                {"symbol": "K", "meaning": "Kop (Keystone Kops)"},
                {"symbol": "L", "meaning": "Lich"},
                {"symbol": "M", "meaning": "Mummy"},
                {"symbol": "N", "meaning": "Naga"},
                {"symbol": "O", "meaning": "Ogre"},
                {"symbol": "P", "meaning": "Pudding or Ooze"},
                {"symbol": "Q", "meaning": "Quantum mechanic"},
                {"symbol": "R", "meaning": "Rust monster"},
                {"symbol": "S", "meaning": "Snake"},
                {"symbol": "T", "meaning": "Troll"},
                {"symbol": "U", "meaning": "Umber hulk"},
                {"symbol": "V", "meaning": "Vampire"},
                {"symbol": "W", "meaning": "Wraith or ghost"},
                {"symbol": "X", "meaning": "Xorn"},
                {"symbol": "Y", "meaning": "Apelike creature"},
                {"symbol": "Z", "meaning": "Zombie"},
                {"symbol": "!", "meaning": "Potion"},
                {"symbol": "\"", "meaning": "Amulet"},
                {"symbol": "#", "meaning": "Iron bars or corridor"},
                {"symbol": "$", "meaning": "Gold piece"},
                {"symbol": "%", "meaning": "Food or corpse"},
                {"symbol": "(", "meaning": "Tool"},
                {"symbol": ")", "meaning": "Weapon"},
                {"symbol": "*", "meaning": "Gem or rock"},
                {"symbol": "[", "meaning": "Armor"},
                {"symbol": "=", "meaning": "Ring"},
                {"symbol": "?", "meaning": "Scroll"},
                {"symbol": "/", "meaning": "Wand"},
            ]
        ]
        
    def init_colors(self):
        """Initialize color pairs used in the UI."""
        curses.start_color()
        curses.use_default_colors()
        
        # Color definitions
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Header
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected item
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Item highlight
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Details
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Search
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)  # Warnings/important
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal text
        
    def setup_screen(self, stdscr):
        """Initialize the screen."""
        self.screen = stdscr
        curses.curs_set(0)  # Hide cursor
        self.screen.keypad(True)  # Enable special keys
        self.init_colors()
        
    def get_category_name(self, category):
        """Get the display name for a category."""
        names = ["Items", "Monsters", "Commands", "Dungeon Features", "Symbols"]
        return names[category.value]
        
    def draw_header(self):
        """Draw the application header."""
        height, width = self.screen.getmaxyx()
        header = " NetHack Reference Guide "
        
        # Center the header
        start_x = (width - len(header)) // 2
        self.screen.addstr(0, 0, " " * width, curses.color_pair(1))
        self.screen.addstr(0, start_x, header, curses.color_pair(1) | curses.A_BOLD)
        
        # Draw categories
        category_y = 1
        for category in Category:
            category_name = self.get_category_name(category)
            if category == self.current_category:
                self.screen.addstr(category_y, 2, f"[{category_name}]", curses.color_pair(3) | curses.A_BOLD)
            else:
                self.screen.addstr(category_y, 2, f" {category_name} ", curses.color_pair(7))
                
            # Move to next position
            category_y += 1
            
        # Search area
        search_prompt = "Search: " + self.search_query
        if self.is_searching:
            self.screen.addstr(category_y + 1, 2, search_prompt, curses.color_pair(5) | curses.A_BOLD)
        else:
            search_help = "Press '/' to search"
            self.screen.addstr(category_y + 1, 2, search_help, curses.color_pair(5))
    
    def draw_item_list(self):
        """Draw the list of items based on current category and filters."""
        height, width = self.screen.getmaxyx()
        
        # Calculate available space for the list
        list_y_start = Category.__len__() + 3  # After header and categories
        list_height = height - list_y_start - 1  # Save 1 row for status bar
        
        # Set max display items
        self.max_display_items = list_height
        
        # Draw items
        for i in range(min(list_height, len(self.filtered_data))):
            item_idx = i + self.scroll_offset
            if item_idx >= len(self.filtered_data):
                break
                
            item = self.filtered_data[item_idx]
            
            # Format display based on category
            if self.current_category == Category.ITEMS:
                display_text = f"{item['symbol']} {item['name']}"
            elif self.current_category == Category.MONSTERS:
                display_text = f"{item['symbol']} {item['name']} (Level {item['level']})"
            elif self.current_category == Category.COMMANDS:
                display_text = f"{item['key']} - {item['action']}"
            elif self.current_category == Category.DUNGEON:
                display_text = f"{item['symbol']} {item['name']}"
            elif self.current_category == Category.SYMBOLS:
                display_text = f"{item['symbol']} - {item['meaning']}"
                
            # Highlight selected item
            if item_idx == self.selected_index:
                self.screen.addstr(list_y_start + i, 2, display_text[:width-4], curses.color_pair(2))
            else:
                self.screen.addstr(list_y_start + i, 2, display_text[:width-4], curses.color_pair(7))
    
    def draw_details(self):
        """Draw details for the selected item."""
        if not self.filtered_data or self.selected_index >= len(self.filtered_data):
            return
            
        height, width = self.screen.getmaxyx()
        item = self.filtered_data[self.selected_index]
        
        # Calculate position for details
        details_y = height - 1
        
        # Show description if available
        if 'description' in item:
            description = item['description']
            # Truncate if necessary
            if len(description) > width - 4:
                description = description[:width-7] + "..."
            self.screen.addstr(details_y, 2, description, curses.color_pair(4))
    
    def draw_status_bar(self):
        """Draw status bar with controls and information."""
        height, width = self.screen.getmaxyx()
        status_text = "↑/↓: Navigate | Tab: Change Category | /: Search | q: Quit"
        
        # Clear the line
        self.screen.addstr(height-2, 0, " " * width, curses.color_pair(1))
        
        # Draw the text
        self.screen.addstr(height-2, 2, status_text, curses.color_pair(1))
    
    def filter_data(self):
        """Filter data based on search query."""
        if not self.search_query:
            self.filtered_data = self.data[self.current_category.value]
            return
            
        # Case-insensitive search
        query = self.search_query.lower()
        
        # Filter based on category
        if self.current_category == Category.ITEMS:
            self.filtered_data = [item for item in self.data[self.current_category.value] 
                                  if query in item['name'].lower() or 
                                  query in item['description'].lower()]
        elif self.current_category == Category.MONSTERS:
            self.filtered_data = [item for item in self.data[self.current_category.value] 
                                  if query in item['name'].lower() or 
                                  query in item['description'].lower()]
        elif self.current_category == Category.COMMANDS:
            self.filtered_data = [item for item in self.data[self.current_category.value] 
                                  if query in item['key'].lower() or 
                                  query in item['action'].lower()]
        elif self.current_category == Category.DUNGEON:
            self.filtered_data = [item for item in self.data[self.current_category.value] 
                                  if query in item['name'].lower() or 
                                  query in item['description'].lower()]
        elif self.current_category == Category.SYMBOLS:
            self.filtered_data = [item for item in self.data[self.current_category.value] 
                                  if query in str(item['symbol']).lower() or 
                                  query in item['meaning'].lower()]
        
        # Reset selection if filtered data is empty
        if not self.filtered_data:
            self.selected_index = 0
            self.scroll_offset = 0
        # Adjust selection if it's out of bounds
        elif self.selected_index >= len(self.filtered_data):
            self.selected_index = len(self.filtered_data) - 1
            self.adjust_scroll()
    
    def adjust_scroll(self):
        """Adjust scroll offset to keep selected item visible."""
        # If selected item is below viewport
        if self.selected_index >= self.scroll_offset + self.max_display_items:
            self.scroll_offset = self.selected_index - self.max_display_items + 1
        # If selected item is above viewport
        elif self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
    
    def handle_input(self):
        """Process user input."""
        try:
            key = self.screen.getch()
            
            # Handle search mode separately
            if self.is_searching:
                if key == 27:  # ESC
                    self.is_searching = False
                    self.search_query = ""
                    self.filter_data()
                elif key == 10:  # Enter
                    self.is_searching = False
                    self.filter_data()
                elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                    self.search_query = self.search_query[:-1]
                    self.filter_data()
                elif 32 <= key <= 126:  # Printable characters
                    self.search_query += chr(key)
                    self.filter_data()
                return
            
            # Normal navigation mode
            if key == ord('q'):
                self.running = False
            elif key == ord('/'):
                self.is_searching = True
                self.search_query = ""
            elif key == 9:  # Tab
                # Switch to next category
                next_value = (self.current_category.value + 1) % len(Category)
                self.current_category = Category(next_value)
                self.selected_index = 0
                self.scroll_offset = 0
                self.filtered_data = self.data[self.current_category.value]
            elif key == curses.KEY_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    self.adjust_scroll()
            elif key == curses.KEY_DOWN:
                if self.selected_index < len(self.filtered_data) - 1:
                    self.selected_index += 1
                    self.adjust_scroll()
            elif key == curses.KEY_PPAGE:  # Page Up
                self.selected_index = max(0, self.selected_index - self.max_display_items)
                self.adjust_scroll()
            elif key == curses.KEY_NPAGE:  # Page Down
                self.selected_index = min(len(self.filtered_data) - 1, 
                                          self.selected_index + self.max_display_items)
                self.adjust_scroll()
            elif key == curses.KEY_HOME:
                self.selected_index = 0
                self.scroll_offset = 0
            elif key == curses.KEY_END:
                self.selected_index = len(self.filtered_data) - 1
                self.adjust_scroll()
                
        except curses.error:
            pass
    
    def refresh_screen(self):
        """Update everything on screen."""
        self.screen.clear()
        self.draw_header()
        self.draw_item_list()
        self.draw_details()
        self.draw_status_bar()
        self.screen.refresh()
    
    def main(self, stdscr):
        """Main application loop."""
        self.setup_screen(stdscr)
        
        while self.running:
            self.refresh_screen()
            self.handle_input()
    
    def run(self):
        """Start the application."""
        curses.wrapper(self.main)

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    curses.endwin()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    app = NethackReferenceTUI()
    app.run()
