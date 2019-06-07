FROM bwa:latest

ENV PATH=/opt/bin:$PATH

COPY bwa.aws.sh /opt/bin/bwa.aws.sh
RUN chmod +x /opt/bin/bwa.aws.sh

WORKDIR /scratch

ENTRYPOINT ["bwa.aws.sh"]
