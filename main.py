# This is a sample Python script.

from  randomy import create_image

if __name__ == '__main__':
    create_image(768, 768 * 2,seed="yourseed")

    for n in range(10):
        create_image(768,768*2)
