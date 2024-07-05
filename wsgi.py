# lomos-api2
# Copyright © 2022-2024 XLAB d.o.o. All rights reserved.

# The lomos-api2 is released under the commercial license.
# Redistribution and use in source and binary forms is not permitted without prior written permission.

from lomos_api2.lomos_api2 import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=25001)
