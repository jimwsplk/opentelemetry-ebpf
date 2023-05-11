#!/bin/bash
# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


buckets=$(aws s3api list-buckets --query 'Buckets[*].{Name:Name}' --output text)
ret="$?"
if [ "${ret}" != "0" ]; then
    echo "Failed to list S3 buckets!"
    exit "${ret}"
fi

header_string="%-50s %-12s %-12s %-16s %-18s\n"
format_string="%-50s %-12s %12s %16s %18s\n"
printf "${format_string}" "Bucket" "Region" "Total Bytes" "Partial Uploads" "Est. Yearly Cost"

for bucket in ${buckets}; do

    region=$(aws s3api get-bucket-location --bucket "${bucket}" --query 'LocationConstraint' --output text 2>/dev/null)
    ret="$?"
    if [ "${ret}" != "0" ]; then
        # Ignore the EERO bucket but nothing else
        if [ "${bucket}" != "eero-telemetry-uw2" ]; then
            echo "Failed to get region for bucket ${bucket}"
            exit "${ref}"
        fi
        continue
    fi
    if [ "${region}" == "None" ]; then
        region="us-east-1"        
    fi

    size=$(aws s3api list-objects --bucket ${bucket} --query "sum(Contents[].Size)" 2>/dev/null)
    ret="$?"
    if [ "${ret}" != "0" ]; then
        # Assume the size is 0 as it's probably the "sum" expression that failed
        printf "${format_string}" ${bucket} ${region} "0B" "0B" "\$0"
        continue
    fi
    size_readable=$(numfmt --to=iec --suffix=B ${size})

    gb=$((1024 * 1024 * 1024))
    estimated_cost="\$$(numfmt --to=si `echo "12 * ${size} * 0.0125 / ${gb}" | bc`)"

    partial_uploads=0
    parts=$(aws s3api list-multipart-uploads --bucket $bucket --region $region --query 'Uploads[*].{Key:Key,UploadId:UploadId}' --output text)
    if [ "$parts" != "None" ]; then
        IFS=$'\n'
        for part in $parts
        do
            keyname=$(echo $part | awk '{print $1}')
            upload_id=$(echo $part | awk '{print $2}')
            id_size=$(aws s3api list-parts --upload-id $upload_id --bucket $bucket --key $keyname | grep "Size" | egrep -o '[0-9]+' | awk 'BEGIN {SUM = 0}; { SUM += $1} END { print SUM }')
            partial_uploads=$(( ${partial_uploads} + ${id_size} ))
        done
    fi

    stranded_space=$(numfmt --to=iec --suffix=B ${partial_uploads})
    printf "${format_string}" ${bucket} ${region} ${size_readable} ${stranded_space} ${estimated_cost}

done
