import tempfile

def test_save(image, suffix):
    with tempfile.NamedTemporaryFile(mode='w+b', suffix=suffix) as f:
        try:
            image.save(f)
        except (OSError, ValueError, KeyError):
            result = False
        else:
            result = True
    
    return result
