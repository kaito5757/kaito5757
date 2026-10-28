"""Draws the contribution calendar as a sunset-colored grid with three pixel pugs playing under it.

Usage:
  GITHUB_TOKEN=... python3 scripts/dog.py <user> <out_dir>
  python3 scripts/dog.py <user> <out_dir> --json calendar.json   # use a saved GraphQL response
Writes <out_dir>/dog-dark.svg and <out_dir>/dog-light.svg.
"""
import json, math, os, sys, urllib.request

QUERY = """query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar {
  weeks { contributionDays { contributionLevel weekday } } } } } }"""
LEVELS = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}

_PUG = dict(white='#f6f4f0', black='#4a4543', line='#1a1716', wrinkle='#b3aca9', shine='#ffffff',
            blush='#f5a3b5', tongue='#f38ba8', heart='#f38ba8', zzz='#cdd6f4')
THEMES = {
    'dark': dict(_PUG, cells=['#2a2537', '#5a3f5e', '#a85a72', '#e3837c', '#f9cb8f'], ground='#4d3650',
                 shadow='#000000'),
    'light': dict(_PUG, cells=['#ebe4e8', '#f4c7cc', '#eba0ac', '#e3837c', '#d9603f'], ground='#d8c6c8',
                  shadow='#8a7f84', zzz='#7c7f93'),
}
# Coat colors: the avatar's white pug, a fawn friend and a silver friend.
COATS = {
    'white': {},
    'fawn': dict(white='#e9c9a1', wrinkle='#c9a27a'),
    'silver': dict(white='#cfc8c2', wrinkle='#a39a94'),
}

STEP, CELL, PAD = 14, 11, 10   # grid
PX = 4                         # dog pixel size
SPRITE_W = 24                  # sprite width in dog pixels (for mirroring)
SCENE = 24                     # seconds for one round of the scene


def fetch(user):
    req = urllib.request.Request('https://api.github.com/graphql',
                                 data=json.dumps({'query': QUERY, 'variables': {'login': user}}).encode(),
                                 headers={'Authorization': 'bearer ' + os.environ['GITHUB_TOKEN'],
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def dog_cells(legs=0, tail=0, patch=True, asleep=False, bow=False):
    """Chibi pug facing right: {(x, y): role}.

    legs/tail pick one of two poses (0/1); asleep lies down with the eyes closed;
    bow is the play bow (front down, rear up) that dogs use to ask "let's play".
    """
    c = {}
    def fill(x0, x1, y0, y1, role):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                c[(x, y)] = role
    fill(5, 12, 7, 11, 'white')        # small body
    fill(12, 15, 9, 11, 'white')       # chest under the head
    if patch:
        fill(7, 9, 7, 7, 'black')      # patch on the back
        c[(8, 8)] = 'black'
    fill(11, 20, 1, 8, 'white')        # big round head
    for xy in [(11, 1), (20, 1), (20, 8)]:
        del c[xy]                      # round the corners (the lower-left one joins the body)
    for x, y in [(11, 1), (12, 1), (10, 2), (11, 2), (19, 1), (20, 1), (21, 2), (20, 2)]:
        c[(x, y)] = 'black'            # floppy ears
    c[(14, 2)] = 'wrinkle'             # little frown
    c[(15, 2)] = 'wrinkle'
    if asleep:
        c[(16, 4)] = c[(17, 4)] = 'line'   # closed eye
    else:
        fill(16, 17, 3, 4, 'black')    # big eye
        c[(16, 3)] = 'shine'
    c[(15, 6)] = 'blush'               # rosy cheek
    c[(16, 6)] = 'blush'
    for x, y in [(18, 5), (19, 5), (20, 5), (18, 6), (19, 6), (20, 6), (21, 6), (18, 7), (19, 7), (20, 7)]:
        c[(x, y)] = 'black'            # muzzle
    if not asleep:
        c[(19, 8)] = 'tongue'
    dy = 0 if tail == 0 else -1        # the tail wags up and down
    for x, y in [(3, 5), (4, 5), (2, 6), (5, 6), (2, 7), (3, 7), (4, 7)]:
        c[(x, y + dy)] = 'white'       # curled tail
    c[(3, 6 + dy)] = 'black'
    c[(4, 6 + dy)] = 'black'
    c[(4, 7)] = 'white'                # tail root stays on the body
    if asleep:
        c = {(x, y + 2): role for (x, y), role in c.items()}   # lie down: no legs, body on the ground
    elif bow:
        c = {(x, y + 2 if x >= 11 else y): role for (x, y), role in c.items()}   # front half down
        for x in [6, 8]:
            c[(x, 12)] = 'black' if (x == 6 and patch) else 'white'
            c[(x, 13)] = 'black'       # hind legs stay up
        c[(16, 13)] = c[(17, 13)] = 'black'   # front paws stretched forward
    else:
        for k, x in enumerate([6, 8, 12, 14] if legs == 0 else [7, 9, 13, 15]):
            c[(x, 12)] = 'black' if (k == 0 and patch) else 'white'
            c[(x, 13)] = 'black'       # black paws (and one dark hind leg)
    # Outline: empty neighbors of the shape, like the hand-drawn avatar.
    out = dict(c)
    for (x, y) in c:
        for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if (x + ddx, y + ddy) not in c:
                out[(x + ddx, y + ddy)] = 'line'
    return out


ZED = [(0, 0), (1, 0), (2, 0), (3, 0), (2, 1), (1, 2), (0, 3), (1, 3), (2, 3), (3, 3)]
BALL = {(1, 0): 'ball', (2, 0): 'ball', (0, 1): 'ball', (1, 1): 'seam', (2, 1): 'ball', (3, 1): 'ball',
        (0, 2): 'ball', (1, 2): 'ball', (2, 2): 'seam', (3, 2): 'ball', (1, 3): 'ball', (2, 3): 'ball'}


def rects(cells, colors, flip=False, dx=0, dy=0, cls=''):
    """One <g> of pixel rects; flip mirrors the sprite to face left."""
    o = ['<g%s>' % (' class="%s"' % cls if cls else '')]
    for (x, y), role in sorted(cells.items()):
        X = (SPRITE_W - 1 - x) if flip else x
        o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>'
                 % ((X + dx) * PX, (y + dy) * PX, PX, PX, colors[role]))
    o.append('</g>')
    return ''.join(o)


def walking(colors, patch, flip=False):
    return ('<g class="bob">' + rects(dog_cells(0, 0, patch), colors, flip, cls='f0')
            + rects(dog_cells(1, 1, patch), colors, flip, cls='f1') + '</g>')


def resting(colors, patch, flip=False):
    """Standing still, wagging the tail."""
    return (rects(dog_cells(0, 0, patch), colors, flip, cls='f0')
            + rects(dog_cells(0, 1, patch), colors, flip, cls='f1'))


def bowing(colors, patch, flip=False):
    """Play bow, bouncing and wagging."""
    return ('<g class="bob">' + rects(dog_cells(0, 0, patch, bow=True), colors, flip, cls='f0')
            + rects(dog_cells(0, 1, patch, bow=True), colors, flip, cls='f1') + '</g>')


def keyframes(name, frames):
    """@keyframes from [(percent, css)]."""
    return '@keyframes %s{%s}' % (name, ''.join('%.2f%%{%s}' % (p, css) for p, css in frames))


def show(name, *spans):
    """Opacity keyframes: visible only during the given (start%, end%) spans."""
    frames = [(0, 'opacity:0')]
    for s, e in spans:
        frames += [(max(s - 0.01, 0), 'opacity:0'), (s, 'opacity:1'), (e - 0.01, 'opacity:1'), (e, 'opacity:0')]
    return keyframes(name, sorted(frames + [(100, 'opacity:0')]))


def render(weeks, theme):
    t = dict(THEMES[theme], ball='#e5f28a', seam='#f6f4f0')
    cols = len(weeks)
    width = PAD * 2 + cols * STEP
    grid_h = 7 * STEP
    ground_y = PAD + grid_h + 96
    height = ground_y + 8
    top = ground_y - 15 * PX + PX      # sprite top so that the paws touch the ground
    coat = {name: dict(t, **c) for name, c in COATS.items()}

    # The scene loops seamlessly: whoever runs off to the right comes back in from the left,
    # and every position is a function of time sampled over the whole loop, so 0% equals 100%.
    # The fawn pug (B) leaves early and is already coming back while the white one (A) is still
    # on screen, so the stage is never empty.
    #   ..-22  the ball rolls in from the left; B and A chase it in, B overtakes it and turns around
    #   22-32  both play-bow: "let's play!"
    #   32-64  the ball flies back and forth; whoever gets it hops to bounce it back
    #   64-..  B kicks the ball off to the right and both chase it, hopping over C (asleep)
    # (B is back on screen at ~93%, before A leaves at ~98%.)
    a_stop = int(width * 0.26)
    b_stop = a_stop + 190
    c_x = int(width * 0.74)
    a_nose = a_stop + 21 * PX          # where the ball meets each dog
    b_nose = b_stop + 2 * PX
    mid = (a_nose + b_nose) // 2
    ball_y = ground_y - 4 * PX - 2
    off_l, off_r = -100, width + 100   # just outside the picture

    def lerp(a, b, f):
        return a + (b - a) * f

    # A runs off during 66-104 (i.e. 4% into the next loop), jumps back to the left while
    # off screen, and walks in during 4-22.
    a_wrap = 4
    v_b = (off_r - b_stop) / 28                    # B: runs off during 64-92
    b_at0 = b_stop - v_b * 22                      # B's position at 0% (already on its way in)
    b_in = 100 - (b_at0 - off_l) / v_b             # B reappears from the left at this %

    def x_a(p):
        if p < a_wrap: return lerp(a_stop, off_r, (p + 100 - 66) / (100 + a_wrap - 66))
        if p < 22: return lerp(off_l, a_stop, (p - a_wrap) / (22 - a_wrap))
        if p < 66: return a_stop
        return lerp(a_stop, off_r, (p - 66) / (100 + a_wrap - 66))

    def x_b(p):
        if p < 22: return lerp(b_at0, b_stop, p / 22)
        if p < 64: return b_stop
        if p < 92: return lerp(b_stop, off_r, (p - 64) / 28)
        if p < b_in: return off_r
        return lerp(off_l, b_at0, (p - b_in) / (100 - b_in))

    def over_c(x):                     # hop over the sleeping C
        d = (x - c_x) / 96
        return -30 * (1 - d * d) if abs(d) < 1 else 0

    def bump(p, *times):               # a little hop when the ball arrives
        for t0 in times:
            if abs(p - t0) < 1.2:
                return -14 * (1 - ((p - t0) / 1.2) ** 2)
        return 0

    def y_a(p):
        return (over_c(x_a(p)) if (p >= 66 or p < a_wrap) else 0) + bump(p, 40, 58)

    def y_b(p):
        return (over_c(x_b(p)) if p >= 64 else 0) + bump(p, 49, 64)

    def arc(p, p0, p1, x0, x1, h):
        f = (p - p0) / (p1 - p0)
        return lerp(x0, x1, f), ball_y - h * 4 * f * (1 - f)

    def ball(p):
        if p < 22 or p >= 90:          # rolls in from the left, slowing down, with small hops
            f = ((p - 90) % 100) / 32
            e = 1 - (1 - f) ** 2
            return lerp(-40, mid, e), ball_y - 14 * (1 - f) * abs(math.sin(3 * math.pi * f))
        if p < 32: return mid, ball_y
        if p < 40: return arc(p, 32, 40, mid, a_nose, 30)
        if p < 49: return arc(p, 40, 49, a_nose, b_nose, 46)
        if p < 58: return arc(p, 49, 58, b_nose, a_nose, 46)
        if p < 64: return arc(p, 58, 64, a_nose, b_nose, 40)
        if p < 82:                     # kicked away with fading bounces
            f = (p - 64) / 18
            return lerp(b_nose, width + 40, f), ball_y - 40 * (1 - f) * abs(math.sin(2.5 * math.pi * f))
        return width + 40, ball_y

    # Sample every 0.5% plus the moments where something starts or stops.
    marks = {k / 2 for k in range(201)} | {a_wrap, b_in, 22, 32, 40, 49, 58, 64, 66, 82, 90, 92}
    marks |= {m - 0.01 for m in (a_wrap, b_in, 90)}
    pts = sorted(m for m in marks if 0 <= m <= 100)

    def track(fn):
        return [(p, fn(p)) for p in pts]

    css = ''.join([
        '.sc{animation-duration:%ds;animation-iteration-count:infinite;animation-timing-function:linear}' % SCENE,
        '.mvA{animation-name:mvA}', keyframes('mvA', [(p, 'transform:translateX(%.1fpx)' % v) for p, v in track(x_a)]),
        '.mvB{animation-name:mvB}', keyframes('mvB', [(p, 'transform:translateX(%.1fpx)' % v) for p, v in track(x_b)]),
        '.hopA{animation-name:hopA}', keyframes('hopA', [(p, 'transform:translateY(%.1fpx)' % v) for p, v in track(y_a)]),
        '.hopB{animation-name:hopB}', keyframes('hopB', [(p, 'transform:translateY(%.1fpx)' % v) for p, v in track(y_b)]),
        '.ball{animation-name:ball}', keyframes('ball', [(p, 'transform:translate(%.1fpx,%.1fpx)' % v)
                                                         for p, v in track(ball)]),
        '.aw{animation-name:aw}', show('aw', (0, 22), (66, 100)),
        '.ab{animation-name:ab}', show('ab', (22, 32)),
        '.ar{animation-name:ar}', show('ar', (32, 66)),
        '.bw{animation-name:bw}', show('bw', (0, 22), (64, 100)),
        '.bb{animation-name:bb}', show('bb', (22, 32)),
        '.br{animation-name:br}', show('br', (32, 64)),
        '.f0{animation:step .5s steps(1) infinite}.f1{animation:step .5s steps(1) infinite;animation-delay:-.25s}',
        '@keyframes step{0%{opacity:1}50%{opacity:0}}',
        '.bob{animation:bob .5s steps(1) infinite}',
        '@keyframes bob{0%%{transform:none}50%%{transform:translateY(-%dpx)}}' % PX,
        '.zz{opacity:0;animation:zz 3s ease-out infinite}',
        '@keyframes zz{0%{opacity:0;transform:none}20%{opacity:1}100%{opacity:0;transform:translate(10px,-18px)}}',
        # Still image: the play bow, ball between them.
        '@media (prefers-reduced-motion:reduce){.sc,.f0,.f1,.bob,.zz{animation:none}.f1,.aw,.ar,.bw,.br{opacity:0}'
        '.ab,.bb,.zz{opacity:1}.mvA{transform:translateX(%dpx)}.mvB{transform:translateX(%dpx)}'
        '.ball{transform:translate(%dpx,%dpx)}}' % (a_stop, b_stop, mid, ball_y),
    ])

    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" '
         'aria-label="contributions" shape-rendering="crispEdges">' % (width, height, width, height),
         '<style>%s</style>' % css]
    for x, week in enumerate(weeks):
        for day in week['contributionDays']:
            level = LEVELS.get(day['contributionLevel'], 0)
            o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s" shape-rendering="auto"/>'
                     % (PAD + x * STEP, PAD + day['weekday'] * STEP, CELL, CELL, t['cells'][level]))
    o.append('<rect x="0" y="%d" width="%d" height="2" fill="%s"/>' % (ground_y, width, t['ground']))

    def shadow():
        return ('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" fill-opacity=".35" shape-rendering="auto"/>'
                % (4 * PX, 14 * PX, 14 * PX, PX + 1, PX, t['shadow']))

    # C: asleep, with z's drifting up.
    o.append('<g transform="translate(%d,%d)">%s' % (c_x, top, shadow()))
    o.append(rects(dog_cells(patch=False, asleep=True), coat['silver']))
    for k in range(3):
        o.append('<g class="zz" style="animation-delay:%ds">' % k)
        o.append(rects({xy: 'zzz' for xy in ZED}, t, dx=19 + k, dy=1 - k * 2))
        o.append('</g>')
    o.append('</g>')

    # A: the avatar's white pug.
    o.append('<g class="sc mvA"><g transform="translate(0,%d)">%s<g class="sc hopA">' % (top, shadow()))
    o.append('<g class="sc aw">%s</g>' % walking(coat['white'], True))
    o.append('<g class="sc ab">%s</g>' % bowing(coat['white'], True))
    o.append('<g class="sc ar">%s</g>' % resting(coat['white'], True))
    o.append('</g></g></g>')

    # B: the fawn friend, facing A (left) only while they play.
    o.append('<g class="sc mvB"><g transform="translate(0,%d)">%s<g class="sc hopB">' % (top, shadow()))
    o.append('<g class="sc bw">%s</g>' % walking(coat['fawn'], False))
    o.append('<g class="sc bb">%s</g>' % bowing(coat['fawn'], False, flip=True))
    o.append('<g class="sc br">%s</g>' % resting(coat['fawn'], False, flip=True))
    o.append('</g></g></g>')

    # The ball.
    o.append('<g class="sc ball">%s</g>' % rects(BALL, t))
    o.append('</svg>')
    return '\n'.join(o)


def main():
    user, out_dir = sys.argv[1], sys.argv[2]
    if '--json' in sys.argv:
        data = json.load(open(sys.argv[sys.argv.index('--json') + 1]))
    else:
        data = fetch(user)
    weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    os.makedirs(out_dir, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(out_dir, 'dog-%s.svg' % theme), 'w') as f:
            f.write(render(weeks, theme))


if __name__ == '__main__':
    main()
