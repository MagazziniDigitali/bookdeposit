from celery import Celery, states
from celery.exceptions import Ignore

import zipfile
import os
import bagit
import subprocess
import glob
import shutil
import re

from bookdeposit.config import config
processed_dir = config.get('server', 'processed_dir')
error_dir = config.get('server', 'error_dir')

from bookdeposit.db import db, Deposit


app = Celery('process', backend='redis://localhost',
             broker='redis://localhost')


@app.task(bind=True)
def validate(self, bag, user):
    bag_upload_dir = os.path.dirname(bag)

    deposit = Deposit.query.filter_by(bag_uuid=self.request.id).first()

    # the zipped bag is decompressed is unzipped into incoming_dir
    with zipfile.ZipFile(bag) as bag_zip:
        bag_zip.extractall(path=bag_upload_dir)
        bag_name = bag_zip.infolist()[0].filename[:-1]
        bag_dir = os.path.join(bag_upload_dir, bag_name)

    try:
        bag = bagit.Bag(bag_dir)
    except bagit.BagError as e:
        shutil.move(os.path.join(bag_upload_dir), os.path.join(
            error_dir, self.request.id))
        # shutil.rmtree(bag_upload_dir)
        self.update_state(state=states.FAILURE, meta=e)

        deposit.status = "FAILURE"
        deposit.errors = str(e)
        db.session.commit()

        raise Ignore()

    try:
        bag.validate()
    except bagit.BagValidationError as e:
        shutil.move(bag_dir,
                    os.path.join(error_dir, self.request.id))
        shutil.rmtree(bag_upload_dir)
        self.update_state(state=states.FAILURE, meta=e)

        deposit.status = "FAILURE"
        deposit.errors = str(e)
        db.session.commit()

        raise Ignore()

    bag.info['BNCF-identifier'] = self.request.id
    bag.info['BNCF-original-bagname'] = bag_name
    bag.info['BNCF-user-id'] = user
    bag.save()

    for payload_file in bag.payload_files():
        # derive and extract, only pdf or epub
        if re.match(".*(pdf|epub)$", payload_file):
            # siegfried
            subprocess.call(
                "sf -json '{0}' | jq . > '{0}.siegfried.json'".format(payload_file), shell=True, cwd=bag_dir)
            # extract text, if allowed in Bagit-Profile-Identifier
            if "Bagit-Profile-Identifier" in bag.info:
                if (bag.info["Bagit-Profile-Identifier"] == "ALLOW_TEXT_EXTRACTION"):
                    subprocess.call(
                        "tika -t '{0}' > '{0}'.txt".format(payload_file), shell=True, cwd=bag_dir)
            # tika metadata - disabled
            # subprocess.call(
            #     "tika -m -j -r '{0}' > '{0}.tika.json'".format(payload_file), shell=True, cwd=bag_dir)

    bag.save(manifests=True)

    # moving processed bag to processed_dir and remove from upload dir
    shutil.move(bag_dir,
                os.path.join(processed_dir, self.request.id))
    shutil.rmtree(bag_upload_dir)

    # create tar file of processed bag and remove the directory
    subprocess.call("tar cf {0}.tar {0}".format(
        self.request.id), cwd=processed_dir, shell=True)
    shutil.rmtree(os.path.join(processed_dir, self.request.id))

    deposit.status = "SUCCESS"
    db.session.commit()

    return "valid bag"
