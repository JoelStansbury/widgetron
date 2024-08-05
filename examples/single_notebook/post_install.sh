if [ -d "~/Desktop" ]; then
    touch ~/Desktop/App_Name.sh
    echo "source $PREFIX/etc/profile.d/conda.sh" >> ~/Desktop/App_Name.sh
    echo "conda activate $PREFIX/" >> ~/Desktop/App_Name.sh
    echo "python -m widgetron_app" >> ~/Desktop/App_Name.sh
    chmod +x ~/Desktop/App_Name.sh
else
    echo "No ~/Desktop directory exists... Skipping shortcut"
fi