from PIL import Image


if IN[0] : 
    paths = IN[0]
    save_path = IN[1]
    frames = [
            Image.open(path).convert('RGB') for path in paths
    ]

    frames[0].save(f'{save_path}/prediction.gif', format='GIF', append_images=frames[1:], save_all=True, duration=100 * len(frames), loop=0)

    OUT = "DONE"