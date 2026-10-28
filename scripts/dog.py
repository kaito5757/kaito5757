"""Draws the contribution calendar as a sunset-colored grid with a pixel shiba walking under it.

Usage:
  GITHUB_TOKEN=... python3 scripts/dog.py <user> <out_dir>
  python3 scripts/dog.py <user> <out_dir> --json calendar.json   # use a saved GraphQL response
Writes <out_dir>/dog-dark.svg and <out_dir>/dog-light.svg.
"""
import json, os, sys, urllib.request

QUERY = """query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar {
  weeks { contributionDays { contributionLevel weekday } } } } } }"""
LEVELS = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}

THEMES = {
    'dark': dict(cells=['#2a2537', '#5a3f5e', '#a85a72', '#e3837c', '#f9cb8f'], ground='#4d3650',
                 body='#f0a35e', leg='#c9773d', cream='#fbe9d7', line='#2b1d24', collar='#e64553'),
    'light': dict(cells=['#ebe4e8', '#f4c7cc', '#eba0ac', '#e3837c', '#d9603f'], ground='#d8c6c8',
                  body='#f0a35e', leg='#c9773d', cream='#fbe9d7', line='#2b1d24', collar='#e64553'),
}

STEP, CELL, PAD = 14, 11, 10   # grid
PX = 3                         # dog pixel size
WALK_SECONDS = 22


def fetch(user):
    req = urllib.request.Request('https://api.github.com/graphql',
                                 data=json.dumps({'query': QUERY, 'variables': {'login': user}}).encode(),
                                 headers={'Authorization': 'bearer ' + os.environ['GITHUB_TOKEN'],
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        return json.load(res)


def dog_cells(frame):
    """Shiba facing right on a 21x13 grid: {(x, y): role}. frame 0/1 moves the legs."""
    c = {}
    def fill(x0, x1, y0, y1, role):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                c[(x, y)] = role
    fill(4, 14, 5, 9, 'body')          # body
    fill(6, 12, 8, 9, 'cream')         # belly
    fill(13, 19, 2, 7, 'body')         # head
    fill(17, 20, 5, 7, 'cream')        # muzzle
    fill(13, 13, 3, 8, 'collar')       # collar
    for x, y in [(14, 0), (14, 1), (15, 1), (18, 0), (18, 1), (17, 1)]:
        c[(x, y)] = 'body'             # ears
    for x, y in [(2, 2), (1, 3), (1, 4), (2, 5), (3, 5), (3, 2)]:
        c[(x, y)] = 'body'             # curled tail
    c[(2, 3)] = 'cream'
    c[(16, 4)] = 'line'                # eye
    c[(20, 5)] = 'line'                # nose
    legs = [5, 7, 11, 13] if frame == 0 else [6, 8, 12, 14]
    for x in legs:
        fill(x, x, 10, 11, 'leg')
    # Outline: empty neighbors of the shape.
    out = dict(c)
    for (x, y) in c:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if (x + dx, y + dy) not in c:
                out[(x + dx, y + dy)] = 'line'
    return out


def render(weeks, theme):
    t = THEMES[theme]
    cols = len(weeks)
    width = PAD * 2 + cols * STEP
    grid_h = 7 * STEP
    ground_y = PAD + grid_h + 46
    height = ground_y + 8
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" '
         'aria-label="contributions" shape-rendering="crispEdges">' % (width, height, width, height)]
    o.append('<style>.walk{animation:walk %ds linear infinite}'
             '@keyframes walk{from{transform:translateX(-80px)}to{transform:translateX(%dpx)}}'
             '.f0{animation:step .5s steps(1) infinite}.f1{animation:step .5s steps(1) infinite;animation-delay:-.25s}'
             '@keyframes step{0%%{opacity:1}50%%{opacity:0}}'
             '@media (prefers-reduced-motion:reduce){.walk{animation:none;transform:translateX(%dpx)}'
             '.f0,.f1{animation:none}.f1{opacity:0}}</style>' % (WALK_SECONDS, width + 10, width // 2))
    for x, week in enumerate(weeks):
        for day in week['contributionDays']:
            level = LEVELS.get(day['contributionLevel'], 0)
            o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s" shape-rendering="auto"/>'
                     % (PAD + x * STEP, PAD + day['weekday'] * STEP, CELL, CELL, t['cells'][level]))
    o.append('<rect x="0" y="%d" width="%d" height="2" fill="%s"/>' % (ground_y, width, t['ground']))
    dog_h = 13 * PX
    # The bottom outline row is nearly invisible, so sink the dog by one pixel to stand on the ground.
    o.append('<g class="walk"><g transform="translate(0,%d)">' % (ground_y - dog_h + PX))
    for frame in (0, 1):
        o.append('<g class="f%d">' % frame)
        for (x, y), role in sorted(dog_cells(frame).items()):
            o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (x * PX, y * PX, PX, PX, t[role]))
        o.append('</g>')
    o.append('</g></g></svg>')
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
