"""Retain exact study artifacts while deduplicating unchanged source and review copies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import study

OMIT={'.playwright-cli','__pycache__','node_modules','target','dist','.git'}


def copy_tree(source,dest):
    shutil.copytree(source,dest,ignore=shutil.ignore_patterns(*OMIT))


def link(target,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.symlink_to(os.path.relpath(target,dest.parent),target_is_directory=target.is_dir())


def digest(file):return hashlib.sha256(file.read_bytes()).hexdigest()


def archive(source,reviews,out):
    schedule=json.loads((source/'schedule.json').read_text())
    cases={c['id']:c for c in json.loads((source/'cases.json').read_text())}
    for spec in schedule:
        if not (source/spec['id']/'controller/result.json').exists():raise RuntimeError('Candidate incomplete: '+spec['id'])
    mapping=json.loads((reviews/'condition-map.json').read_text())
    if len(list(reviews.glob('batch-*/review.json')))!=9:raise RuntimeError('Expected nine completed review artifacts')
    out.mkdir(parents=True,exist_ok=False)
    for file in source.iterdir():
        if file.is_file():shutil.copy2(file,out/file.name)
    for name in ['sources','skills','tool-help','runner-preflight']:
        if (source/name).exists():copy_tree(source/name,out/name)
    run_results=[];notes=[]
    for spec in schedule:
        original=source/spec['id'];dest=out/spec['id'];dest.mkdir()
        copy_tree(original/'controller',dest/'controller')
        result=json.loads((original/'controller/result.json').read_text());run_results.append(result)
        candidate=dest/'candidate';candidate.mkdir()
        for entry in (original/'candidate').iterdir():
            if entry.name in OMIT or entry.name in ['app','skill','tool-help']:continue
            if entry.is_dir():copy_tree(entry,candidate/entry.name)
            else:shutil.copy2(entry,candidate/entry.name)
        for name,source_id in cases[spec['case_id']].get('sources',{}).items():
            actual=original/'candidate/app'/name;canonical=out/'sources'/source_id
            if study.hashes(actual)==study.hashes(canonical):link(canonical,candidate/'app'/name)
            else:
                copy_tree(actual,candidate/'app'/name)
                notes.append({'run':spec['id'],'retained_distinct_source':name})
        if (original/'candidate/skill').exists():
            canonical=out/'skills'/f"{spec['surface']}-exploratory-testing"
            if study.hashes(original/'candidate/skill')==study.hashes(canonical):link(canonical,candidate/'skill')
            else:
                copy_tree(original/'candidate/skill',candidate/'skill')
                notes.append({'run':spec['id'],'retained_distinct_skill':True})
        if (original/'candidate/tool-help').exists():link(out/'tool-help',candidate/'tool-help')
    review_out=out/'reviews';review_out.mkdir()
    for file in reviews.iterdir():
        if file.is_file():shutil.copy2(file,review_out/file.name)
    for batch in sorted(reviews.glob('batch-*')):
        dest=review_out/batch.name;dest.mkdir()
        for entry in batch.iterdir():
            if entry.is_file():shutil.copy2(entry,dest/entry.name)
            elif entry.name.startswith('case-'):
                original_candidate=out/mapping[entry.name]['id']/'candidate'
                for file in entry.rglob('*'):
                    if not file.is_file() or any(p in OMIT for p in file.relative_to(entry).parts):continue
                    relative=file.relative_to(entry);target=dest/entry.name/relative
                    target.parent.mkdir(parents=True,exist_ok=True)
                    equivalent=original_candidate/relative
                    if equivalent.is_file() and digest(file)==digest(equivalent):link(equivalent,target)
                    else:shutil.copy2(file,target)
    study.write_json(out/'run-results.json',run_results)
    study.write_json(out/'archive-notes.json',notes)
    entries={}
    for file in sorted(out.rglob('*')):
        if file.is_symlink() and file.is_dir():
            entries[str(file.relative_to(out))]={'symlink':os.readlink(file),'directory':True}
        elif file.is_file():
            entries[str(file.relative_to(out))]={'sha256':digest(file),'bytes':file.stat().st_size,
                                               **({'symlink':os.readlink(file)} if file.is_symlink() else {})}
    study.write_json(out/'artifact-index.json',entries)
    print(json.dumps({'runs':len(run_results),'indexed_files':len(entries),'archive':str(out)}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--reviews',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();archive(a.source.resolve(),a.reviews.resolve(),a.out.resolve())
