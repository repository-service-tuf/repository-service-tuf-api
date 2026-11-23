def test_version_info():
    import repository_service_tuf_api.__version__ as version_module
    
    assert hasattr(version_module, "version")
    assert hasattr(version_module, "copyright")
    assert hasattr(version_module, "author")
    
    assert isinstance(version_module.version, str)
    assert isinstance(version_module.copyright, str)
    assert isinstance(version_module.author, str)
