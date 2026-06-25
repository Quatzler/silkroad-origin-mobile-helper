import cv2
import os

def extract_templates():
    # Login Template
    login_img = cv2.imread('screenshots/01-sro_login.jpeg')
    if login_img is not None:
        # Mitte extrahieren (z.B. Silkroad Logo Bereich)
        h, w = login_img.shape[:2]
        template = login_img[h//4:h//2, w//4:3*w//4]
        os.makedirs('templates/login', exist_ok=True)
        cv2.imwrite('templates/login/logo.png', template)
        print("Login template saved.")

    # Game Template
    game_img = cv2.imread('screenshots/02-sro-game.jpeg')
    if game_img is not None:
        # Suchen nach etwas spezifischem für Game (z.B. Minimap oben rechts)
        h, w = game_img.shape[:2]
        # Oben rechts Bereich
        template = game_img[10:120, w-120:w-10]
        os.makedirs('templates/game', exist_ok=True)
        cv2.imwrite('templates/game/minimap_area.png', template)
        print("Game template saved.")

    # Inventory Template (Back Button)
    inv_img = cv2.imread('screenshots/03-sro-inventory.jpeg')
    if inv_img is not None:
        # Oben links Bereich (Zurück Button)
        template = inv_img[5:80, 5:80]
        os.makedirs('templates/inventory', exist_ok=True)
        cv2.imwrite('templates/inventory/back_button.png', template)
        print("Inventory template saved.")

if __name__ == "__main__":
    extract_templates()
