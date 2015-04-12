# Protocol
# ========
#
# This class handles the basic protocols that tesseract uses to communicate
# with the client. You can read how the protocol works in the documentation
# under Appendix > Server Protocol.
class Protocol:

    # Successful response
    # -------------------
    @staticmethod
    def successful_response(data=None, warnings=None):
        # If there is no data to be returned (for instance a `DELETE` statement)
        # then you should provide `None`.
        assert data is None or isinstance(data, list), '%r' % data

        # Warning are of course optional.
        assert warnings is None or isinstance(warnings, list), '%r' % warnings

        # Build the response.
        response = {
            "success": True
        }
        if data is not None:
            response['data'] = data
        if warnings is not None:
            response['warnings'] = warnings

        return response


    # Failed response
    # ---------------
    @staticmethod
    def failed_response(error):
        # The error message must exist and be a string.
        assert isinstance(error, str), '%r' % error

        # The response is very simple in this case.
        return {
            "success": False,
            "error": error
        }
