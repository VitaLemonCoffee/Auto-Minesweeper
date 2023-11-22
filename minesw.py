from random import randint
from time import sleep
from autopy import *
from PIL import Image
from PIL import ImageGrab as ImG
from PIL import ImageFilter as ImF


class data:
    ''' Store basic data'''
    mode = None  # 0-Easy 1-Medium 2-Expert
    mode_translate = {0: "Easy", 1: "Medium", 2: "Expert"}
    daily = False
    '''
    _pixel_size = [[660, 660], [660, 660], [1237, 660]]
    _pixel_start = [[439, 204], [439, 204], [150, 202]]
    _pixel_size2k = [[],[860,860],[1612,861]]
    _pixel_start2k = [[],[603,215],[226,214]]
    '''
    _widthList = [9, 16, 30]
    _heightList = [9, 16, 16]
    _rest_mines = [10, 40, 99]

    '''
    if screen.scale() == 2.0:
        _pixel_start,_pixel_size=_pixel_start2k,_pixel_size2k
    '''

    # To be initialized in Init()
    pixel_size = [1, 1]
    pixel_start = [1, 1]
    width = 1  # How many cells in each row
    height = 1  # How many cells in each column
    cell_width = 1
    cell_height = 1

    new_game_loc = (660, 810)  # Locate the position of the new game button for 1080p
    new_game_loc2k = (1008, 941)
    scale = screen.scale()  # Translate the position in autopy and screen solution
    difference_accept = 300  # For color_identification

    minemap = None  # To be initialized in main
    rest_mines = None
    known_cells = set()  # Stores known cells' location in (x,y)
    judging_cells = set()  # Stores judging cells' location in (x,y)
    valueless_cells = set()  # Stores the cells' location that is going to be removed from judging_cells
    #
    judge_count = 0
    by_cells = set()
    infer_cells = set()
    infer_count = 0
    #

    img_list = [Image.open('./cell_pics/0.png').convert('RGB'),
                Image.open('./cell_pics/1.png').convert('RGB'),
                Image.open('./cell_pics/2.png').convert('RGB'),
                Image.open('./cell_pics/3.png').convert('RGB'),
                Image.open('./cell_pics/4.png').convert('RGB'),
                Image.open('./cell_pics/5.png').convert('RGB'),
                Image.open('./cell_pics/6.png').convert('RGB'),
                Image.open('./cell_pics/7.png').convert('RGB'),
                Image.open('./cell_pics/8.png').convert('RGB'),
                Image.open('./cell_pics/9.png').convert('RGB')]
    color_param_list = []

class MineMap:
    ''' A Class for assembling the cells'''

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.mine_map = []  # Stores the cells objects in a single list sorted by position

    def add_cell(self, one_cell):
        index = len(self.mine_map)
        if len(self.mine_map) == self.width * self.height:
            index = one_cell.x + self.width * one_cell.y
            self.mine_map.pop(index)
        self.mine_map.insert(index, one_cell)

    def get_cell(self, x, y):
        return self.mine_map[x + self.width * y]

    def get_cell_from(self, xytuple):
        return self.get_cell(xytuple[0], xytuple[1])

    def print_map(self, click_set, debug=True):
        if not debug:
            return
        for y in range(self.height):
            for x in range(self.width):
                temp = self.get_cell(x, y).val
                if temp == 10:
                    print('*', '  ', end = '')
                elif 9 > temp > 0:
                    print(temp, '  ', end = '')
                elif temp == 0:
                    print(' ', '  ', end = '')
                elif (x,y) in click_set:
                    print('! ', ' ', end= '')
                else:
                    print('@@', ' ', end = '')
            print()


class cell:
    ''' A class for cells in minemap'''

    def __init__(self, val, x, y):
        if val == 8: # Trying to be lazy about color_identifier debugging
            val = 5
        self.val = val  # 9 = untapped, 0~8= how many mines around, 10= mine
        self.x = x
        self.y = y
        self.isInfer = False
        self.infer_mine = set()  # If isInfer is True infer_mine will be a set of locations
        self.infer_num = 0  # If isInfer is True infer_num will be the possible mines in infer_mine
        self.mine_chance = 0  # The chance of it being a mine
        data.minemap.add_cell(self)
        if self.val == 10:
            data.rest_mines -= 1
        if self.val == 9:
            self.update()
        else:
            data.known_cells.add((x, y))
        if 9 > self.val > 0 and len(self.get_surround_untapped()) > 0:
            data.judging_cells.add((x, y))

    def update(self):
        if self.val != 9:
            return
        if 0 != data.width * data.height - len(data.known_cells):
            general_chance = data.rest_mines / (data.width * data.height - len(data.known_cells))
            if self.mine_chance < general_chance:
                self.mine_chance = general_chance

    def get_surround_untapped(self):
        ''' Returns a set of untapped cells location in surround 3X3 area'''
        surround_cells = set()
        for a in [-1, 0, 1]:
            for b in [-1, 0, 1]:
                if (a == b == 0 or self.x + a not in range(data.width) or self.y + b not in range(data.height)):
                    continue
                temp_cell = data.minemap.get_cell(self.x + a, self.y + b)
                if temp_cell.val == 9:
                    surround_cells.add((self.x + a, self.y + b))
        return surround_cells

    def count_surround_mines(self):
        ''' Counts the known mines in surround'''
        mine_count = 0
        for a in [-1, 0, 1]:
            for b in [-1, 0, 1]:
                if (a == b == 0 or self.x + a not in range(data.width) or self.y + b not in range(data.height)):
                    continue
                temp_cell = data.minemap.get_cell(self.x + a, self.y + b)
                if temp_cell.val == 10:
                    mine_count += 1
        return mine_count

    def get_inferring_cells(self):
        ''' Resturns a set of locations in the 5X5 area without the corners'''
        inferring_cells = set()
        for a in [-2, -1, 0, 1, 2]:
            for b in [-2, -1, 0, 1, 2]:
                if ((a in [-2, 2] and b in [-2, 2])
                        or a == b == 0
                        or self.x + a not in range(data.width)
                        or self.y + b not in range(data.height)):
                    continue
                temp_cell = data.minemap.get_cell(self.x + a, self.y + b)
                if temp_cell.isInfer:
                    inferring_cells.add((temp_cell.x, temp_cell.y))
        return inferring_cells

    def infer(self, mine_num, untapped_set):
        ''' Returns a set of location that is safe by inferring the possible mines around'''
        last_len = len(untapped_set)
        infer_set = self.get_inferring_cells()
        click_set = set()
        for i in infer_set:
            temp = data.minemap.get_cell_from(i)
            if temp.infer_mine.issubset(untapped_set):
                untapped_set.difference_update(temp.infer_mine)
                mine_num += 1
        if len(untapped_set) == 0 or len(untapped_set) == last_len:
            return click_set
        data.infer_count += 1  # For efficiency test
        if self.val - mine_num == len(untapped_set):
            for c in untapped_set:
                cell(10, c[0], c[1])  # Mark all surrounded untapped cells as mines
        elif self.val - mine_num == 0:
            for c in untapped_set:
                the_cell = data.minemap.get_cell_from(c)
                click_set.add((the_cell.x, the_cell.y))  # This means all surrounded untapped cells are safe to click
        data.infer_cells.update(click_set)
        return click_set

    def judge(self):
        ''' Returns a set of location that is safe and mark the mine_chance of surround cells'''
        mine_num = self.count_surround_mines()
        untapped_set = self.get_surround_untapped()
        click_set = set()
        if len(untapped_set) == 0:
            data.valueless_cells.add((self.x, self.y))
            return click_set
        data.judge_count += 1  # For efficiency test
        if self.val - mine_num == len(untapped_set):
            for c in untapped_set:
                the_cell = data.minemap.get_cell_from(c)
                cell(10, the_cell.x, the_cell.y)  # Mark all surrounded untapped cells as mines
            data.valueless_cells.add((self.x, self.y))
        elif self.val - mine_num == 0:
            for c in untapped_set:
                the_cell = data.minemap.get_cell_from(c)
                click_set.add((the_cell.x, the_cell.y))  # This means all surrounded untapped cells are safe to click
            data.valueless_cells.add((self.x, self.y))
        else:
            if len(untapped_set) > 1:
                click_set.update(self.infer(mine_num, untapped_set))
                untapped_set.difference_update(click_set)
            if len(untapped_set) > 0:
                MC = (self.val - mine_num) / len(untapped_set)
                for c in untapped_set:
                    the_cell = data.minemap.get_cell_from(c)
                    if the_cell.mine_chance < MC:
                        the_cell.mine_chance = MC
                self.isInfer = True
                self.infer_mine = untapped_set.difference(click_set)
                self.infer_num = self.val - mine_num
        if len(click_set) > 0:
            data.by_cells.add((self.x, self.y))
        return click_set


def find_board(im = None):
    def is_good(pxl):
        r, g, b = pxl
        return r > 150 or g < 180 or b < 250
    if im is None:
        im = ImG.grab()
    hori = im.size[0]//2
    vert = im.size[1]//2

    bottom = im.size[1]-1
    c = 0
    while is_good(im.getpixel((hori, bottom))) and bottom >= vert:
        bottom -= 1
    while bottom < vert:
        c += 3
        bottom = im.size[1] - 1
        while is_good(im.getpixel((hori+c, bottom))) and bottom >= vert:
            bottom -= 1

    c = 0
    left = 0
    right = im.size[0]-1
    while is_good(im.getpixel((left, vert))) and left <= hori:
        left += 1
    while is_good(im.getpixel((right, vert))) and right >= hori:
        right -= 1
    while left > hori or right < hori:
        c += 3
        left = 0
        right = im.size[0] - 1
        while is_good(im.getpixel((left, vert + c))) and left <= hori:
            left += 1
        while is_good(im.getpixel((right, vert + c))) and right >= hori:
            right -= 1
    padding = 5
    bottom += padding + 4
    right += padding
    left -= padding
    if bottom > right - left:
        up = bottom - (right - left)
    else:
        up = bottom - (right - left)*(16/30)
    box = (left, up, right, bottom)
    print(box)
    #im.crop(box).show()
    return box


def init(mode = 1):
    """For initialization of minemap and data"""

    data.minemap = None  # To be initialized in main
    data.rest_mines = None
    data.known_cells = set()  # Stores known cells' location in (x,y)
    data.judging_cells = set()  # Stores judging cells' location in (x,y)
    data.valueless_cells = set()  # Stores the cells' location that is going to be removed from judging_cells

    data.mode = mode
    for i in data.img_list:
        w, h = i.size
        data.color_param_list.append(get_main_color(i.crop(tuple(map(int, (0.2*w,0.2*h,0.8*w,0.8*h))))))
    box = find_board(ImG.grab())  # (left, up, right, bottom)
    mode = data.mode
    data.pixel_size = (box[2] - box[0], box[3] - box[1])
    data.pixel_start = (box[0], box[1])
    data.width = data._widthList[mode]  # How many cells in each row
    data.height = data._heightList[mode]  # How many cells in each column
    data.cell_width = data.pixel_size[0] / data.width
    data.cell_height = data.pixel_size[1] / data.height
    data.rest_mines = data._rest_mines[mode]
    data.minemap = MineMap(data.width, data.height)

    for a in range(data.width):
        for b in range(data.height):
            cell(9, a, b)


def cell_crop(x, y, map_img):
    ''' Returns the cropped cell image at x,y'''
    h = data.cell_height
    w = data.cell_width
    return map_img.crop((data.pixel_start[0] + (x + 0.2) * w,
                         data.pixel_start[1] + (y + 0.2) * h,
                         data.pixel_start[0] + (x + 0.8) * w,
                         data.pixel_start[1] + (y + 0.8) * h))


def get_cell_pos(x, y):
    ''' Returns the up-left corner's pixel location of (x,y) in a tuple'''
    x, y = int(x), int(y)
    if (x < 0 or y < 0 or x >= data.width or y >= data.width):
        raise ValueError('get_cell_pos gets wrong parameter')
    return (data.pixel_start[0] + x * data.cell_width,
            data.pixel_start[1] + y * data.cell_height)


def click_cells(cell_set = None):
    ''' Clicks a list of cell through tuples of locations'''
    if cell_set is None:
        cell_set = {(randint(0, data.width - 1), randint(0, data.height - 1))}
    for cell in cell_set:
        click_cell(cell[0], cell[1])


def click_cell(x = None, y= None):
    ''' Clicks the middle part of the cell at (x,y) in mode cell'''
    if x is None and y is None:
        x = randint(0, data.width - 1)
        y = randint(0, data.height - 1)
    x, y = int(x), int(y)
    if (x < 0 or y < 0 or x >= data.width or y >= data.width):
        raise ValueError('click_cell gets wrong parameter')
    loc = get_cell_pos(x, y)
    mouse.move((loc[0] + 0.5 * data.cell_width) / data.scale, (loc[1] + 0.5 * data.cell_height) / data.scale)
    mouse.click()


def get_avg(avg_list):
    ''' Returns average for color data lists'''
    raw = list(filter(lambda x: max(x) - min(x) > 5, avg_list))
    avg = []
    for i in range(3):
        j = list(map(lambda x: x[i], raw))
        if len(j) == 0:
            avg.append(255)
        else:
            avg.append(sum(j) / len(j))
    avg.append(len(raw))
    return avg


def get_main_color(img):
    ''' Returns the color (in list of length 3) of the center part of the cell image'''
    img = img.resize((28,28), Image.ANTIALIAS)
    collist = list(img.getdata())
    col = get_avg(collist)
    return col


def compare_color(img1):
    ''' Return a relative value to show the difference between two images'''
    c1 = get_main_color(img1)
    result_list = []
    for i in data.color_param_list:
        sum = 0
        for j in range(len(c1)-1):
            sum += abs((i[j] - c1[j]) / 2)
        result_list.append(sum / 3)
    if c1[0]>205:
        result_list[5]=300
    return result_list


def color_identifier(img):
    ''' Returns the number ( -1 for untapped and 0 for void) in the image by color'''
    result_list = compare_color(img)
    n = result_list.index(min(result_list))
    if result_list[n] > data.difference_accept:
        # img.show()
        print('Cannot Identify the image with difference of ' + str(result_list[n]))
    return n


def get_hash(img):
    ''' Generate a hash code for a img that indicates its shape'''
    image = img.resize((41, 41), Image.ANTIALIAS).convert("L")
    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)
    return "".join(map(lambda p: "1" if p > avg else "0", pixels))


def print_hash(hash, width):
    for i in range(int(len(hash) / width)):
        print(hash[i * width:(i + 1) * width])


def update_img(raw_img = None, mode = 0):  # Input Image should be 'RGB'
    ''' Update minemap through screenshot'''
    # raw_img=raw_img.convert('L')
    if raw_img is None:
        raw_img = ImG.grab()
    # h = data.cell_height
    # w = data.cell_width
    # raw_img.crop((data.pixel_start[0],
    #               data.pixel_start[1],
    #               int(data.pixel_start[0] + data.pixel_size[0]),
    #               int(data.pixel_start[1] + data.pixel_size[1]))).show()

    if mode == 0:
        for x in range(data.width):
            for y in range(data.height):
                if (x, y) in data.known_cells: continue
                grab_img = cell_crop(x, y, raw_img)
                cell(color_identifier(grab_img), x, y)
    else:
        raise ValueError("mode value error")
    return


def judge(debug=True):
    ''' Returns the cell positions set that should be tapped next'''
    click_set = set()
    new_click = -1
    infer_flag = 1
    for c in data.judging_cells:
        click_set.update(data.minemap.get_cell_from(c).judge())
    for val_c in data.valueless_cells:
        data.judging_cells.discard(val_c)
    data.valueless_cells.clear()
    while len(click_set) - new_click > 0 and infer_flag:
        new_click = len(click_set)
        for c in data.judging_cells:
            click_set.update(data.minemap.get_cell_from(c).judge())
        for val_c in data.valueless_cells:
            data.judging_cells.discard(val_c)
        data.valueless_cells.clear()

    if len(click_set) == 0:
        lowest = 1
        lucky_cells = set()  # cell location
        the_cell = None
        for c in set(data.minemap.mine_map):
            c.update()
            if c.mine_chance <= lowest and c.val == 9:
                if c.mine_chance < lowest:
                    lowest = c.mine_chance
                    lucky_cells=set()
                lucky_cells.add((c.x,c.y))
                the_cell = c
        if lucky_cells:
            click_set.add(lucky_cells.pop())
        else:
            print("Nothing")
            return
        print('LUCKY!', the_cell.mine_chance)

    if debug:
        print('known cells:', len(data.known_cells))
        print('judging cells:', len(data.judging_cells))
        print('judge number:', data.judge_count)
        data.judge_count = 0
        print('infer number:', data.infer_count)
        data.infer_count = 0
        print('mines left:', data.rest_mines)
        print('how many to click:', len(click_set))
        print('by which cells:', data.by_cells)
        data.by_cells.clear()
        print('click cells:', click_set)
        print('infer cells:', data.infer_cells)
        data.infer_cells.clear()
        print()
    return click_set


def color_stat_print():
    init(1)
    for i in range(len(data.color_param_list)):
        print(i, data.color_param_list[i])


def run_mine(modenum = 1, sleepnum = 0.6, debug = True):
    while True:
        if mouse.location() == (0, 0):
            start_mine(modenum, sleepnum, debug)
        else:
            sleep(0.5)
    #mouse.move(data.new_game_loc[0] / data.scale, data.new_game_loc[1] / data.scale)
    #mouse.click()


def start_mine(modenum = 1, sleepnum = 0.6, debug = True):
    sleep_time = sleepnum
    init(modenum)  # 0-Easy 1-Medium 2-Expert
    print(data.mode_translate.get(data.mode))
    update_img(ImG.grab())
    if len(data.known_cells) == 0:
        click_cell()
        sleep(sleep_time)
        update_img(ImG.grab())
    data.minemap.print_map(set(), debug)
    print()
    while len(data.known_cells) < data.width * data.height:
        click_set = judge(debug)
        data.minemap.print_map(click_set, debug)
        click_cells(click_set)
        sleep(sleep_time)
        update_img(ImG.grab())


# https://zone.msn.com/gameplayer/gameplayerHTML.aspx?game=msminesweeper
if __name__ == '__main__':
    run_mine(2)  # 0-Easy 1-Medium 2-Expert
