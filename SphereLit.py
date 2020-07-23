'''
P-uppgift av Otto Lindstam i kursen DD1331 HT2019.
Uppgift 101 - belysning av klot.
Använt bibliotek för grafikfönster är Pyxel av Takashi Kitao.
Använda referenser är
exempelkod och API-instruktioner för Pyxel: https://github.com/kitao/pyxel,
wikipedia för ellipsens ekvation: https://en.wikipedia.org/wiki/Ellipse,
boken Introduction to Programming in Python av Sedgewick, Wayne & Dondero.
Alt+Enter för fullskärm.
'''

# Standard library imports
import math

# Third party imports
import pyxel


#############
# Constants #
#############

WIDTH = 100  # max 256
HEIGHT = 100  # max 256
BG_COL = 3  # 0 to 15
SHADOW_COL = 0
X_STEPS = 1  # "Meta pixel" size
Y_STEPS = 1
R_STEP = 3  # Incriment of radius change on keystroke


class Vec:
    """Create a vector object for organizing collections of x,y,z,b values."""

    def __init__(self, x=0, y=0, z=0, b=0):
        """Define dimensions."""
        self.x = x
        self.y = y
        self.z = z
        self.b = b

    def __add__(self, other):
        """Define addition behaviour."""
        self.x = self.x + other.x
        self.y = self.y + other.y
        self.z = self.z + other.z
        self.b = self.b + other.b
        return self

    def __sub__(self, other):
        """Define subtraction behaviour."""
        self.x = self.x - other.x
        self.y = self.y - other.y
        self.z = self.z - other.z
        self.b = self.b - other.b
        return self

    def __mul__(self, other):
        """Define multiplication behaviour."""
        self.x = other * self.x
        self.y = other * self.y
        self.z = other * self.z
        self.b = self.b
        return self

    def __str__(self):
        """Define print behaviour."""
        return '[{}, {}, {}, {}]'.format(self.x, self.y, self.z, self.b)

# Set origin vector to middle of draw window.
ORIGIN = Vec(WIDTH//2, HEIGHT//2, 0, 0)


#########
# Model #
#########

class Sphere(object):
    """
    Sphere object class.
    Create a lit sphere centered to (0,0,0) based on radius r and
    x,y coordinates of light direction lightDir = Vec(x0,y0). Call update method to
    run lighting model. Results saved to self.vectors as Vec(x,y,z,brightness).
    """

    def __init__(self):
        """Initialize Sphere with default radius and lighting direction."""
        self.r = WIDTH//4
        self.lightDir = Vec()
        self.vectors = []
        self.mask = []
        self.shadow = []

    def inclusion(self):
        """Update list of screen coordinates included in sphere."""
        self.vectors = []
        self.mask = []
        for x in range(-self.r, self.r):
            for y in range(-self.r, self.r):
                if (x**2 + y**2 - self.r**2) < 0:
                    self.vectors.append(Vec(x, y, 0, 0))
                    self.mask.append([x, y])

    def project(self, point):
        """
        Projection to sphere.
        Calculate a z-value projected to sphere based on radius and
        x,y coordinates. Return a Vec(x,y,z)
        """
        projected = Vec(point.x, point.y, int(math.sqrt(abs(self.r**2
                    - point.x**2 - point.y**2)+1)))
        return projected

    def project_all(self):
        """
        Project all points in sphere screen area to sphere surface.
        Output new list of vectors to draw
        """
        temp = []
        projected = Vec()
        for point in self.vectors:
            if point.x % X_STEPS == 0 and point.y % Y_STEPS == 0:
                projected = self.project(point)
                point.z = projected.z
                temp.append(point)
        self.vectors = temp

    def brightness(self):
        """
        Brightness model.
        Calculate the brightness per pixel x,y or intervals of x,y,
        based on x,y,z coordinates and lighting direction lightDir.
        Return a Vec(x,y,z,b)
        """
        temp = []
        for point in self.vectors:
            brightness = int(abs(((self.lightDir.x*point.x + self.lightDir.y*point.y
                          + self.lightDir.z*point.z)/(self.r**2)+1))*8-1)
            for dx in range(X_STEPS):
                for dy in range(Y_STEPS):
                    temp.append(Vec(point.x+dx, point.y+dy, 0, brightness))
        self.vectors = temp



    def shadow_project(self):
        """Generate list of vectors for drawing sphere shadow, based on r, lightDir."""
        # Calculate points for defining elliptical shadows foci and center.
        el_f1 = Vec(0, 0, 0, 0)
        el_c = Vec(int(-self.r * self.lightDir.x / self.lightDir.z), int(-self.r * self.lightDir.y
                   / self.lightDir.z), 0, 0)
        el_f2 = Vec(el_c.x*2, el_c.y*2, 0, 0)

        # Update list of shadow pixels.
        self.shadow = []
        for x in range(-WIDTH, WIDTH):
            for y in range(-HEIGHT, HEIGHT):
                if math.sqrt((x-el_f1.x)**2 + (y-el_f1.y)**2) \
                        + math.sqrt((x-el_f2.x)**2 + (y-el_f2.y)**2) \
                        <= ((2*self.r**2)/self.lightDir.z):  # Ellipse formula
                    self.shadow.append(Vec(x, y, 0, SHADOW_COL))

    def update(self):
        """
        Update the sphere lighting model.
        Results in array of vectors with pixel values to draw.
        """
        self.inclusion()
        self.lightDir = self.project(self.lightDir)
        self.project_all()
        self.brightness()
        self.shadow_project()

        # Add shadowcoordinates to beginning of vector list, so drawn below
        self.shadow += self.vectors
        self.vectors = self.shadow


###########
# Control #
###########

class SphereApp(object):
    """Class for interfacing with Sphere lighting model."""

    def __init__(self):
        """Set up and run the simulation with GUI."""
        # Make grayscale color palette
        myPalette = []
        for i in range(0, 16777216, 16777216 // 15):
            myPalette.append(i)

        # Initialize Pyxel GUI
        pyxel.init(WIDTH, HEIGHT, caption="Sphere Lighting",
                   scale=6, palette=myPalette)
        pyxel.mouse(True)

        # Instantiate sphere object
        self.my_sphere = Sphere()
        self.pointer = Vec()

        # Create the first frame by updating sphere model and drawing unlit sphere
        self.my_sphere.update()
        self.draw_empty()

        # Continuously update the sphere model, real time sim runs here.
        self.update()

    def update(self):
        """Update sphere objects lighting model depending on user input."""
        while True:
            # Shift mouse pointer coordinates to (0,0)-relative for sphere model
            self.pointer = Vec(pyxel.mouse_x, pyxel.mouse_y, 0, 0)
            self.my_sphere.lightDir = self.pointer - ORIGIN

            # Update lighting based on mouse position
            if [self.pointer.x, self.pointer.y] in self.my_sphere.mask:
                self.my_sphere.update()
                self.draw()

            # Quit on Q key
            if pyxel.btn(pyxel.KEY_Q):
                pyxel.quit()

            # Increase radius on up arrow key
            if pyxel.btn(pyxel.KEY_UP) and self.my_sphere.r < (HEIGHT//2):
                self.my_sphere.lightDir = Vec(0, 0)
                self.my_sphere.r += R_STEP
                self.my_sphere.update()

            # Decrease radius on down arrow key
            if pyxel.btn(pyxel.KEY_DOWN) and self.my_sphere.r > 5:
                self.my_sphere.lightDir = Vec(0, 0)
                self.my_sphere.r -= R_STEP
                self.my_sphere.update()

            # Draw unlit scene
            self.draw_empty()


    ########
    # View #
    ########

    def draw(self):
        """Draw sphere at viewport center."""
        pyxel.cls(BG_COL)  # Clear screen
        for point in self.my_sphere.vectors:
            px_out = point + ORIGIN
            pyxel.pset(px_out.x, px_out.y, px_out.b)
        self.draw_hud()
        pyxel.flip() # Progress pyxel

    def draw_hud(self):
        """Print heads up display and pixels from sphere object."""
        pyxel.text(0, HEIGHT//1.05, "Q -> Quit | arrows -> rad", 7)

    def draw_empty(self):
        """Draw unlit scene."""
        pyxel.flip()  # Progress pyxel
        pyxel.cls(BG_COL)  # Clear screen
        pyxel.circ(ORIGIN.x,ORIGIN.y,self.my_sphere.r,SHADOW_COL)
        self.draw_hud()

def main():
    """Run the program."""
    SphereApp()


if __name__ == "__main__":
    main()
