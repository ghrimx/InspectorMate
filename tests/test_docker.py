
def test_docker():
    import docker
    client = docker.from_env()
    # image = client.images.pull('gotenberg/gotenberg')
    # f = open('gotenber.tar', 'wb')
    # for chunk in image.save():
    #     f.write(chunk)
    #     f.close()